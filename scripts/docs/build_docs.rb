#!/usr/bin/env ruby
# frozen_string_literal: true

require "cgi"
require "fileutils"
require "json"
require "optparse"
require "pathname"
require "time"
require "uri"
require "yaml"

require_relative "../jekyll_markdown_renderer"

DOCS_SCOPE_CONFIG_PATH = File.expand_path("docs_scopes.json", __dir__)
DOCS_SCOPE_CONFIG_SCHEMA_VERSION = "docs_scopes_v1"
DOCS_VIEWER_BROWSER_CONFIG_PATH = File.expand_path("../../assets/docs-viewer/data/docs-viewer-config.json", __dir__)
DOCS_VIEWER_BROWSER_CONFIG_SCHEMA_VERSION = "docs_viewer_config_v1"

ScopeConfig = Struct.new(
  :scope_id,
  :source,
  :media_path_prefix,
  :output,
  :viewer_base_url,
  :include_scope_param,
  :default_doc_id,
  :allow_nested_source,
  :non_loadable_doc_ids,
  :manage_only_tree_root_ids,
  :show_updated_date,
  :allow_unresolved_parent_ids,
  keyword_init: true
)

DocRecord = Struct.new(
  :scope_id,
  :doc_id,
  :title,
  :added_date,
  :last_updated,
  :summary,
  :ui_status,
  :parent_id,
  :sort_order,
  :published,
  :hidden,
  :viewable,
  :source_path,
  :viewer_url,
  :content_url,
  :body_markdown,
  keyword_init: true
)

class DocsDataBuilder
  FRONT_MATTER_PATTERN = /\A---\s*\n(.*?)\n---\s*\n?/m.freeze
  MEDIA_TOKEN_PATTERN = /\[\[media:(.+?)\]\]/.freeze
  SCRIPT_STYLE_PATTERN = %r{<\s*(script|style)\b[^>]*>.*?<\s*/\s*\1\s*>}im.freeze
  SVG_PATTERN = %r{<svg\b.*?</svg>}im.freeze
  SVG_TEXT_PATTERN = %r{<(title|desc|text)\b[^>]*>(.*?)</\s*\1\s*>}im.freeze
  IMG_PATTERN = %r{<img\b([^>]*)>}i.freeze
  BLOCK_BOUNDARY_PATTERN = %r{</?(article|aside|blockquote|div|figcaption|figure|footer|h[1-6]|header|li|main|ol|p|section|table|tr|ul)\b[^>]*>}i.freeze
  TAG_PATTERN = /<[^>]+>/m.freeze

  def initialize(
    scope_id:,
    source_dir:,
    output_dir:,
    viewer_base_url:,
    include_scope_param: false,
    allow_nested_source: false,
    non_loadable_doc_ids: [],
    manage_only_tree_root_ids: [],
    show_updated_date: true,
    allow_unresolved_parent_ids: false
  )
    @scope_id = scope_id.to_s
    @source_dir = Pathname(source_dir).expand_path
    @output_dir = Pathname(output_dir).expand_path
    @items_dir = @output_dir.join("by-id")
    @viewer_base_url = normalize_viewer_base_url(viewer_base_url)
    @include_scope_param = include_scope_param
    @allow_nested_source = allow_nested_source
    @non_loadable_doc_ids = normalize_doc_ids(non_loadable_doc_ids)
    @manage_only_tree_root_ids = normalize_doc_ids(manage_only_tree_root_ids)
    @show_updated_date = show_updated_date != false
    @allow_unresolved_parent_ids = allow_unresolved_parent_ids == true
    @repo_root = Pathname(__dir__).parent.parent.realpath
    @output_url_base = output_url_base_for(@output_dir)
    @site_config = load_site_config
  end

  def run(write:)
    docs = load_docs
    validate_docs!(docs)

    item_payloads = docs.to_h { |doc| [doc.doc_id, item_entry(doc, docs)] }
    docs_index = docs.sort_by { |doc| doc_sort_key(doc) }.map { |doc| index_entry(doc, docs, item_payloads[doc.doc_id]) }
    viewer_options = viewer_options_payload
    index_payload = {
      "generated_at" => effective_generated_at(docs_index, viewer_options),
      "viewer_options" => viewer_options,
      "docs" => docs_index
    }
    write_plan = build_write_plan(index_payload, item_payloads)

    unless write
      dry_run_summary(index_payload, item_payloads, write_plan)
      return {
        index_payload: index_payload,
        item_payloads: item_payloads,
        write_plan: write_plan
      }
    end

    write_outputs(index_payload, item_payloads, write_plan)
    {
      index_payload: index_payload,
      item_payloads: item_payloads,
      write_plan: write_plan
    }
  end

  private

  def normalize_viewer_base_url(viewer_base_url)
    normalized = viewer_base_url.to_s.strip
    normalized = "/docs/" if normalized.empty?
    normalized = "/#{normalized}" unless normalized.start_with?("/")
    normalized.end_with?("/") ? normalized : "#{normalized}/"
  end

  def normalize_doc_ids(values)
    Array(values).map { |value| value.to_s.strip }.reject(&:empty?).uniq.sort
  end

  def viewer_options_payload
    {
      "non_loadable_doc_ids" => @non_loadable_doc_ids,
      "manage_only_tree_root_ids" => @manage_only_tree_root_ids,
      "show_updated_date" => @show_updated_date
    }
  end

  def load_docs
    all_paths = Dir.glob(@source_dir.join("**/*.md").to_s).sort.map { |file_path| Pathname(file_path) }
    nested_paths = all_paths.select { |path| path.dirname != @source_dir }
    if !@allow_nested_source && !nested_paths.empty?
      nested_list = nested_paths.map { |path| path.relative_path_from(@source_dir).to_s }.join(", ")
      raise "Nested markdown docs are not supported under #{@source_dir}; move these files to the scope root: #{nested_list}"
    end

    all_paths.filter_map do |path|
      relative_path = path.relative_path_from(@source_dir).to_s
      front_matter, body_markdown = parse_source(path)
      next if unpublished_doc?(front_matter)

      stem = path.basename(".md").to_s
      doc_id = (front_matter["doc_id"] || stem).to_s
      title = (front_matter["title"] || extract_title(body_markdown) || humanize(stem)).to_s
      parent_id = front_matter.key?("parent_id") ? front_matter["parent_id"].to_s : ""
      last_updated = front_matter["last_updated"] ? front_matter["last_updated"].to_s : ""
      added_date = front_matter["added_date"] ? front_matter["added_date"].to_s : last_updated
      summary = normalize_summary(front_matter["summary"])
      ui_status = normalize_ui_status(front_matter["ui_status"])
      sort_order = normalize_sort_order(front_matter["sort_order"])
      published = true
      hidden = hidden_front_matter_value(front_matter)
      viewable = !hidden

      DocRecord.new(
        scope_id: @scope_id,
        doc_id: doc_id,
        title: title,
        added_date: added_date,
        last_updated: last_updated,
        summary: summary,
        ui_status: ui_status,
        parent_id: parent_id,
        sort_order: sort_order,
        published: published,
        hidden: hidden,
        viewable: viewable,
        source_path: relative_path,
        viewer_url: viewer_url_for(doc_id),
        content_url: content_url_for(doc_id),
        body_markdown: body_markdown
      )
    end
  end

  def parse_source(path)
    raw = path.read
    match = raw.match(FRONT_MATTER_PATTERN)
    return [{}, raw] unless match

    front_matter = YAML.safe_load(match[1], permitted_classes: [Date, Time], aliases: false) || {}
    body = raw.sub(FRONT_MATTER_PATTERN, "")
    [front_matter, body]
  end

  def unpublished_doc?(front_matter)
    !boolean_front_matter_value(front_matter, "published", true)
  end

  def boolean_front_matter_value(front_matter, key, default)
    return default unless front_matter.key?(key)

    value = front_matter[key]
    return value if value == true || value == false

    !%w[false 0 no off].include?(value.to_s.strip.downcase)
  end

  def hidden_front_matter_value(front_matter)
    return boolean_front_matter_value(front_matter, "hidden", false) if front_matter.key?("hidden")

    !boolean_front_matter_value(front_matter, "viewable", true)
  end

  def extract_title(markdown)
    markdown.each_line do |line|
      stripped = line.strip
      return Regexp.last_match(1).strip if stripped.match(/\A#\s+(.+?)\s*\z/)
    end

    nil
  end

  def humanize(value)
    value.to_s.tr("_-", " ").split.map(&:capitalize).join(" ")
  end

  def normalize_sort_order(value)
    return nil if value.nil? || value.to_s.strip.empty?

    Integer(value)
  rescue ArgumentError, TypeError
    raise "Invalid sort_order #{value.inspect}; expected an integer"
  end

  def normalize_summary(value)
    value.to_s.gsub(/\s+/, " ").strip
  end

  def normalize_ui_status(value)
    value.to_s.strip
  end

  def viewer_url_for(doc_id, anchor = nil)
    query_pairs = []
    query_pairs << "scope=#{CGI.escape(@scope_id)}" if @include_scope_param && !@scope_id.empty?
    query_pairs << "doc=#{CGI.escape(doc_id.to_s)}"
    url = "#{@viewer_base_url}?#{query_pairs.join('&')}"
    anchor.to_s.empty? ? url : "#{url}##{anchor}"
  end

  def content_url_for(doc_id)
    "#{@output_url_base}/by-id/#{CGI.escape(doc_id.to_s)}.json"
  end

  def validate_docs!(docs)
    duplicate_ids = docs.group_by(&:doc_id).select { |_doc_id, group| group.length > 1 }
    raise "Duplicate doc_id values: #{duplicate_ids.keys.join(', ')}" unless duplicate_ids.empty?

    docs.each do |doc|
      next if doc.parent_id.empty?
      next if docs.any? { |candidate| candidate.doc_id == doc.parent_id }
      next if @allow_unresolved_parent_ids

      raise "Unknown parent_id #{doc.parent_id.inspect} for doc #{doc.doc_id.inspect}"
    end
  end

  def effective_parent_id(doc, docs)
    parent_id = doc.parent_id.to_s
    return parent_id if parent_id.empty?
    return parent_id if docs.any? { |candidate| candidate.doc_id == parent_id }

    @allow_unresolved_parent_ids ? "" : parent_id
  end

  def index_entry(doc, docs, item_payload)
    entry = {
      "scope" => doc.scope_id,
      "doc_id" => doc.doc_id,
      "title" => doc.title,
      "added_date" => doc.added_date,
      "last_updated" => doc.last_updated,
      "parent_id" => effective_parent_id(doc, docs),
      "sort_order" => doc.sort_order,
      "published" => doc.published,
      "hidden" => doc.hidden,
      "viewable" => doc.viewable,
      "source_path" => doc.source_path,
      "viewer_url" => doc.viewer_url,
      "content_url" => doc.content_url,
      "content_text_length" => plain_text_from_rendered_html(
        item_payload ? item_payload["content_html"] : "",
        title: doc.title
      ).length
    }
    entry["summary"] = doc.summary unless doc.summary.empty?
    entry["ui_status"] = doc.ui_status unless doc.ui_status.empty?
    entry
  end

  def item_entry(doc, docs)
    entry = {
      "scope" => doc.scope_id,
      "doc_id" => doc.doc_id,
      "title" => doc.title,
      "added_date" => doc.added_date,
      "last_updated" => doc.last_updated,
      "parent_id" => effective_parent_id(doc, docs),
      "sort_order" => doc.sort_order,
      "published" => doc.published,
      "hidden" => doc.hidden,
      "viewable" => doc.viewable,
      "source_path" => doc.source_path,
      "viewer_url" => doc.viewer_url,
      "content_html" => rewrite_doc_links(
        JekyllMarkdownRenderer.render_string(resolve_media_tokens(doc.body_markdown)),
        current_doc: doc,
        docs: docs
      )
    }
    entry["summary"] = doc.summary unless doc.summary.empty?
    entry["ui_status"] = doc.ui_status unless doc.ui_status.empty?
    entry
  end

  def plain_text_from_rendered_html(content_html, title:)
    text = content_html.to_s
      .gsub(SCRIPT_STYLE_PATTERN, " ")
      .gsub(SVG_PATTERN) { |svg| image_marker(svg.scan(SVG_TEXT_PATTERN).map { |match| match[1] }.join(" ")) }
      .gsub(IMG_PATTERN) { image_marker(html_attribute(Regexp.last_match(1), "alt")) }
      .gsub(/<br\b[^>]*>/i, "\n")
      .gsub(BLOCK_BOUNDARY_PATTERN, "\n")
      .gsub(TAG_PATTERN, " ")

    lines = CGI.unescapeHTML(text)
      .lines
      .map { |line| line.gsub(/\s+/, " ").strip }
      .reject(&:empty?)
    lines.shift if !lines.empty? && lines.first == title.to_s.strip
    lines.join("\n").strip
  end

  def image_marker(text)
    normalized = text.to_s.gsub(/\s+/, " ").strip
    normalized.empty? ? "[image]" : "[image: #{CGI.unescapeHTML(normalized)}]"
  end

  def html_attribute(raw_attrs, name)
    match = raw_attrs.to_s.match(/\b#{Regexp.escape(name)}\s*=\s*(["'])(.*?)\1/im)
    match ? match[2] : ""
  end

  def rewrite_doc_links(html, current_doc:, docs:)
    docs_by_id = docs.to_h { |doc| [doc.doc_id, doc] }
    docs_by_source = docs.to_h { |doc| [doc.source_path, doc] }
    docs_by_repo_path = docs.to_h do |doc|
      [@source_dir.join(doc.source_path).cleanpath.to_s, doc]
    end

    html.gsub(/href=(["'])(.*?)\1/) do
      quote = Regexp.last_match(1)
      href = Regexp.last_match(2)
      rewritten = rewrite_href(
        href,
        current_doc: current_doc,
        docs_by_id: docs_by_id,
        docs_by_source: docs_by_source,
        docs_by_repo_path: docs_by_repo_path
      )
      %(href=#{quote}#{rewritten}#{quote})
    end
  end

  def rewrite_href(href, current_doc:, docs_by_id:, docs_by_source:, docs_by_repo_path:)
    return href if href.empty? || href.start_with?("#", "mailto:")
    return href if href.match?(/\A[a-z][a-z0-9+\-.]*:/i)

    begin
      parsed = URI.parse(href)
    rescue URI::InvalidURIError
      return href
    end

    path_part = parsed.path.to_s
    query_values = CGI.parse(parsed.query.to_s)
    anchor = parsed.fragment
    return href if path_part.empty?

    viewer_doc_id = query_values.fetch("doc", []).first.to_s
    if !viewer_doc_id.empty? && viewer_path_match?(path_part, query_values)
      target_doc = docs_by_id[viewer_doc_id]
      return target_doc ? viewer_url_for(target_doc.doc_id, anchor) : href
    end

    if path_part.start_with?(@repo_root.to_s)
      target_doc = docs_by_repo_path[path_part]
      return target_doc ? viewer_url_for(target_doc.doc_id, anchor) : href
    end

    return href unless path_part.end_with?(".md")

    current_dir = Pathname(current_doc.source_path).dirname
    resolved_path = current_dir.join(path_part).cleanpath.to_s
    target_doc = docs_by_source[resolved_path]
    target_doc ? viewer_url_for(target_doc.doc_id, anchor) : href
  end

  def viewer_path_match?(path_part, query_values)
    explicit_scope = query_values.fetch("scope", []).first.to_s
    return false if !explicit_scope.empty? && explicit_scope != @scope_id
    return true if path_part == @viewer_base_url

    viewer_scope_for_path(path_part) == @scope_id
  end

  def viewer_scope_for_path(path_part)
    @viewer_scope_for_path ||= load_scope_configs.to_h do |config|
      normalized = config.viewer_base_url.to_s.strip
      normalized = "/#{normalized}" unless normalized.start_with?("/")
      normalized = "#{normalized}/" unless normalized.end_with?("/")
      [normalized, config.scope_id]
    end
    normalized_path = path_part.to_s.strip
    normalized_path = "/#{normalized_path}" unless normalized_path.start_with?("/")
    normalized_path = "#{normalized_path}/" unless normalized_path.end_with?("/")
    @viewer_scope_for_path.fetch(normalized_path, "")
  end

  def doc_sort_key(doc)
    [
      doc.sort_order.nil? ? 1 : 0,
      doc.sort_order || 0,
      doc.title.downcase,
      doc.doc_id
    ]
  end

  def effective_generated_at(docs_index, viewer_options)
    existing_payload = load_json_file(@output_dir.join("index.json"))
    return Time.now.utc.iso8601 unless existing_payload.is_a?(Hash)

    existing_docs = existing_payload["docs"]
    existing_viewer_options = existing_payload["viewer_options"]
    existing_generated_at = existing_payload["generated_at"].to_s
    return Time.now.utc.iso8601 unless existing_docs == docs_index
    return Time.now.utc.iso8601 unless existing_viewer_options == viewer_options
    return Time.now.utc.iso8601 if existing_generated_at.empty?

    existing_generated_at
  end

  def write_outputs(index_payload, item_payloads, write_plan)
    write_payload_set(@output_dir, @items_dir, index_payload, item_payloads, write_plan)
  end

  def dry_run_summary(index_payload, item_payloads, write_plan)
    puts "Dry run:"
    puts "  scope: #{@scope_id}"
    puts "  source: #{@source_dir}"
    puts "  docs: #{index_payload.fetch("docs").length}"
    puts "  would write index: #{write_plan[:index_write] ? 1 : 0}"
    puts "  would write doc payloads: #{write_plan[:changed_item_ids].length}"
    puts "  would remove stale doc payloads: #{write_plan[:stale_item_ids].length}"
  end

  def write_payload_set(output_dir, items_dir, index_payload, item_payloads, write_plan, label: nil)
    FileUtils.mkdir_p(output_dir)
    FileUtils.mkdir_p(items_dir)

    index_path = output_dir.join("index.json")
    write_text(index_path, write_plan[:index_text]) if write_plan[:index_write]

    write_plan[:changed_item_ids].each do |doc_id|
      write_text(items_dir.join("#{doc_id}.json"), write_plan[:item_text_by_id].fetch(doc_id))
    end

    write_plan[:stale_item_ids].each do |doc_id|
      FileUtils.rm_f(items_dir.join("#{doc_id}.json"))
    end

    prefix = label ? "#{label}: " : ""
    puts "#{prefix}Docs JSON done for scope #{@scope_id}."
    puts "#{prefix}Index wrote: #{write_plan[:index_write] ? 1 : 0}. Path: #{index_path}"
    puts "#{prefix}Doc payloads wrote: #{write_plan[:changed_item_ids].length}. Path: #{items_dir}"
    puts "#{prefix}Doc payloads removed: #{write_plan[:stale_item_ids].length}. Path: #{items_dir}"
  end

  def build_write_plan(index_payload, item_payloads)
    index_text = json_text(index_payload)
    existing_index_text = read_text(@output_dir.join("index.json"))
    changed_item_ids = []
    item_text_by_id = {}

    item_payloads.each do |doc_id, payload|
      item_text = json_text(payload)
      item_text_by_id[doc_id] = item_text
      existing_item_text = read_text(@items_dir.join("#{doc_id}.json"))
      changed_item_ids << doc_id if existing_item_text != item_text
    end

    existing_item_ids = existing_doc_payload_ids(@items_dir)
    desired_item_ids = item_payloads.keys.sort

    {
      index_write: existing_index_text != index_text,
      index_text: index_text,
      changed_item_ids: changed_item_ids.sort,
      stale_item_ids: (existing_item_ids - desired_item_ids).sort,
      item_text_by_id: item_text_by_id
    }
  end

  def existing_doc_payload_ids(items_dir)
    return [] unless items_dir.exist?

    Dir.glob(items_dir.join("*.json").to_s).sort.map do |file_path|
      Pathname(file_path).basename(".json").to_s
    end
  end

  def read_text(path)
    return nil unless path.exist?

    path.read
  end

  def write_text(path, text)
    path.write(text)
  end

  def json_text(payload)
    JSON.pretty_generate(payload) + "\n"
  end

  def load_json_file(path)
    return nil unless path.exist?

    JSON.parse(path.read)
  rescue JSON::ParserError
    nil
  end

  def output_url_base_for(output_dir)
    relative_path = output_dir.relative_path_from(@repo_root).to_s
    "/#{relative_path}"
  end

  def load_site_config
    config_path = @repo_root.join("_config.yml")
    return {} unless config_path.exist?

    YAML.safe_load(config_path.read, permitted_classes: [Date, Time], aliases: false) || {}
  end

  def resolve_media_tokens(markdown)
    return markdown unless markdown.include?("[[media:")

    markdown.gsub(MEDIA_TOKEN_PATTERN) do
      resolve_media_url(Regexp.last_match(1))
    end
  end

  def resolve_media_url(raw_path)
    relative_path = raw_path.to_s.strip
    return "" if relative_path.empty?

    if relative_path.match?(/\A[a-z][a-z0-9+\-.]*:\/\//i)
      return relative_path
    end

    media_base = @site_config.fetch("media_base", "").to_s.strip
    clean_path = relative_path.sub(%r{\A/+}, "")
    return "/#{clean_path}" if media_base.empty?

    "#{media_base.sub(%r{/+\z}, '')}/#{clean_path}"
  end
end

def normalize_scope_config_path(value, label)
  text = value.to_s.strip
  raise "Docs scope config field #{label} is required" if text.empty?

  path = Pathname(text)
  if path.absolute? || path.each_filename.any? { |part| part == ".." }
    raise "Docs scope config field #{label} must be a safe relative path"
  end
  text
end

def normalize_scope_config_array(value, label)
  raise "Docs scope config field #{label} must be an array" unless value.nil? || value.is_a?(Array)

  Array(value).map { |item| item.to_s.strip }.reject(&:empty?)
end

def normalized_browser_viewer_base_url(value)
  text = value.to_s.strip
  text = "/docs/" if text.empty?
  text = "/#{text}" unless text.start_with?("/")
  text.end_with?("/") ? text : "#{text}/"
end

def browser_docs_index_url(config)
  "/#{config.output.sub(%r{\A/+}, "")}/index.json"
end

def browser_search_index_url(config)
  "/assets/data/search/#{config.scope_id}/index.json"
end

def browser_search_policy_payload(config)
  {
    "domain" => "docs_viewer",
    "schema" => "search_index_#{config.scope_id}_v1",
    "index_url" => browser_search_index_url(config),
    "targeted_policy" => "record_update",
    "targeted_operations" => %w[create update delete]
  }
end

def browser_scope_config_payload(scope_configs)
  payload = {
    "schema_version" => DOCS_VIEWER_BROWSER_CONFIG_SCHEMA_VERSION,
    "default_scope_id" => scope_configs.first&.scope_id.to_s,
    "scopes" => scope_configs.map do |config|
      {
        "scope_id" => config.scope_id,
        "viewer_base_url" => normalized_browser_viewer_base_url(config.viewer_base_url),
        "include_scope_param" => config.include_scope_param == true,
        "default_doc_id" => config.default_doc_id,
        "media_path_prefix" => config.media_path_prefix,
        "index_url" => browser_docs_index_url(config),
        "search_index_url" => browser_search_index_url(config),
        "search" => browser_search_policy_payload(config)
      }
    end
  }
  docs_scope_payload = JSON.parse(File.read(DOCS_SCOPE_CONFIG_PATH))
  docs_viewer_settings = docs_scope_payload["docs_viewer"]
  if docs_viewer_settings.is_a?(Hash)
    payload["docs_viewer"] = docs_viewer_settings
  end
  payload
end

def write_docs_viewer_browser_config(scope_configs)
  payload = browser_scope_config_payload(scope_configs)
  FileUtils.mkdir_p(File.dirname(DOCS_VIEWER_BROWSER_CONFIG_PATH))
  File.write(DOCS_VIEWER_BROWSER_CONFIG_PATH, JSON.pretty_generate(payload) + "\n")
  puts "Docs Viewer browser config wrote: #{DOCS_VIEWER_BROWSER_CONFIG_PATH}"
end

def load_scope_configs(path = DOCS_SCOPE_CONFIG_PATH)
  payload = JSON.parse(File.read(path))
  unless payload.is_a?(Hash) && payload["schema_version"] == DOCS_SCOPE_CONFIG_SCHEMA_VERSION
    raise "Docs scope config schema_version must be #{DOCS_SCOPE_CONFIG_SCHEMA_VERSION}"
  end
  scopes = payload["scopes"]
  raise "Docs scope config scopes must be an array" unless scopes.is_a?(Array)

  seen = {}
  scopes.each_with_index.map do |item, index|
    raise "Docs scope config scopes[#{index}] must be an object" unless item.is_a?(Hash)

    scope_id = item["scope_id"].to_s.strip.downcase
    default_doc_id = item["default_doc_id"].to_s.strip
    raise "Docs scope config scopes[#{index}].scope_id is required" if scope_id.empty?
    raise "Docs scope config scopes[#{index}].default_doc_id is required" if default_doc_id.empty?
    raise "Docs scope config scope_id #{scope_id.inspect} is duplicated" if seen[scope_id]

    seen[scope_id] = true
    ScopeConfig.new(
      scope_id: scope_id,
      source: normalize_scope_config_path(item["source"], "scopes[#{index}].source"),
      media_path_prefix: normalize_scope_config_path(
        item["media_path_prefix"] || "docs/#{scope_id}",
        "scopes[#{index}].media_path_prefix"
      ),
      output: normalize_scope_config_path(item["output"], "scopes[#{index}].output"),
      viewer_base_url: item["viewer_base_url"].to_s,
      include_scope_param: item["include_scope_param"] == true,
      default_doc_id: default_doc_id,
      allow_nested_source: item["allow_nested_source"] == true,
      non_loadable_doc_ids: normalize_scope_config_array(
        item["non_loadable_doc_ids"],
        "scopes[#{index}].non_loadable_doc_ids"
      ),
      manage_only_tree_root_ids: normalize_scope_config_array(
        item["manage_only_tree_root_ids"],
        "scopes[#{index}].manage_only_tree_root_ids"
      ),
      show_updated_date: item["show_updated_date"] != false,
      allow_unresolved_parent_ids: item["allow_unresolved_parent_ids"] == true
    )
  end
end

options = {
  scopes: [],
  source: nil,
  output: nil,
  viewer_base_url: nil,
  write: false
}

OptionParser.new do |parser|
  parser.banner = "Usage: ./scripts/build_docs.rb [options]"

  parser.on("--scope NAME", "Limit build to a named docs scope (repeatable)") do |value|
    options[:scopes] << value.to_s.strip.downcase
  end

  parser.on("--source PATH", "Override docs source directory for a single selected scope") do |value|
    options[:source] = value
  end

  parser.on("--output PATH", "Override docs data output directory for a single selected scope") do |value|
    options[:output] = value
  end

  parser.on("--viewer-base-url URL", "Override viewer page URL base for a single selected scope") do |value|
    options[:viewer_base_url] = value
  end

  parser.on("--write", "Write generated files") do
    options[:write] = true
  end
end.parse!

scope_configs = load_scope_configs

selected_scopes = scope_configs.select do |config|
  options[:scopes].empty? || options[:scopes].include?(config.scope_id)
end

raise "Unknown docs scope(s): #{options[:scopes].join(', ')}" if selected_scopes.empty?

if [options[:source], options[:output], options[:viewer_base_url]].any? && selected_scopes.length != 1
  raise "--source, --output, and --viewer-base-url can only be used when exactly one scope is selected"
end

write_docs_viewer_browser_config(scope_configs) if options[:write]

selected_scopes.each do |config|
  builder = DocsDataBuilder.new(
    scope_id: config.scope_id,
    source_dir: options[:source] || config.source,
    output_dir: options[:output] || config.output,
    viewer_base_url: options[:viewer_base_url] || config.viewer_base_url,
    include_scope_param: config.include_scope_param,
    allow_nested_source: config.allow_nested_source,
    non_loadable_doc_ids: config.non_loadable_doc_ids,
    manage_only_tree_root_ids: config.manage_only_tree_root_ids,
    show_updated_date: config.show_updated_date,
    allow_unresolved_parent_ids: config.allow_unresolved_parent_ids
  )
  builder.run(write: options[:write])
end
