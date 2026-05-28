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

require_relative "../../studio/shared/ruby/jekyll_markdown_renderer"

DOCS_SCOPE_CONFIG_PATH = File.expand_path("../config/scopes/docs_scopes.json", __dir__)
DOCS_SCOPE_CONFIG_SCHEMA_VERSION = "docs_scopes_v1"
DOCS_VIEWER_BROWSER_CONFIG_PATH = File.expand_path("../config/defaults/docs-viewer-config.json", __dir__)
DOCS_VIEWER_PUBLIC_BROWSER_CONFIG_PATH = File.expand_path("../config/defaults/docs-viewer-public-config.json", __dir__)
DOCS_VIEWER_BROWSER_CONFIG_SCHEMA_VERSION = "docs_viewer_config_v1"
DOCS_VIEWER_MANAGE_ROUTE_BASE_URL = "/docs/"

ScopeConfig = Struct.new(
  :scope_id,
  :scope_type,
  :source,
  :media_path_prefix,
  :output,
  :search_output,
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
  :hidden,
  :viewable,
  :source_path,
  :viewer_url,
  :content_url,
  :viewer_report,
  :viewer_report_scope,
  :viewer_report_access,
  :viewer_report_preset,
  :body_markdown,
  keyword_init: true
)

SemanticRefToken = Struct.new(
  :raw,
  :kind,
  :id,
  :label,
  :action,
  :modifier_error,
  keyword_init: true
)

class FrontMatterSyntaxError < StandardError; end

class DocsDataBuilder
  FRONT_MATTER_PATTERN = /\A---\s*\n(.*?)\n---\s*\n?/m.freeze
  MEDIA_TOKEN_PATTERN = /\[\[media:(.+?)\]\]/.freeze
  INTERACTIVE_HTML_TOKEN_PATTERN = /\[\[interactive-html:(.+?)\]\]/.freeze
  SEMANTIC_REF_TOKEN_PATTERN = /\[\[ref:(.*?)\]\](\{[^}\n]*\})?/m.freeze
  SEMANTIC_REF_ALLOWED_ACTIONS = %w[link].freeze
  SEMANTIC_REF_SUPPORTED_KINDS = %w[work series moment].freeze
  INTERACTIVE_HTML_FILENAME_PATTERN = /\A[a-z0-9][a-z0-9._-]*\.html\z/i.freeze
  INTERACTIVE_HTML_HEIGHT_PATTERN = /\A[1-9][0-9]{0,3}\z/.freeze
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
    allow_unresolved_parent_ids: false,
    only_doc_ids: nil
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
    @only_doc_ids = only_doc_ids.nil? ? nil : normalize_doc_ids(only_doc_ids)
    @repo_root = Pathname(__dir__).parent.parent.realpath
    @output_url_base = output_url_base_for(@output_dir)
    @site_config = load_site_config
    @source_files_scanned = 0
    @warnings = []
  end

  def run(write:)
    started_at = monotonic_time
    @warnings = []
    docs = load_docs
    validate_docs!(docs)

    target_doc_ids = targeted_build? ? @only_doc_ids : docs.map(&:doc_id)
    validate_targeted_build_prerequisites!(docs, target_doc_ids) if targeted_build?
    semantic_references_by_doc = targeted_build? ? existing_reference_records_by_doc(docs, target_doc_ids) : {}
    docs_for_item_build = docs.select { |doc| target_doc_ids.include?(doc.doc_id) }
    item_payloads = docs_for_item_build.to_h do |doc|
      [doc.doc_id, item_entry(doc, docs, semantic_references_by_doc)]
    end
    docs_for_item_build.each { |doc| semantic_references_by_doc[doc.doc_id] ||= [] }
    docs_index = docs.sort_by { |doc| doc_sort_key(doc) }.map { |doc| index_entry(doc, docs, item_payloads[doc.doc_id]) }
    viewer_options = viewer_options_payload
    index_payload = {
      "generated_at" => effective_generated_at(docs_index, viewer_options),
      "viewer_options" => viewer_options,
      "docs" => docs_index
    }
    reference_payloads = build_reference_payloads(docs, semantic_references_by_doc)
    write_plan = build_write_plan(index_payload, item_payloads, reference_payloads, target_doc_ids: targeted_build? ? target_doc_ids : nil)

    unless write
      dry_run_summary(index_payload, item_payloads, reference_payloads, write_plan)
      diagnostics = diagnostics_payload(
        docs: docs,
        write_plan: write_plan,
        elapsed_seconds: elapsed_seconds_since(started_at),
        target_doc_ids: targeted_build? ? target_doc_ids : nil
      )
      print_diagnostics(diagnostics)
      return {
        index_payload: index_payload,
        item_payloads: item_payloads,
        reference_payloads: reference_payloads,
        write_plan: write_plan,
        diagnostics: diagnostics
      }
    end

    write_outputs(index_payload, item_payloads, reference_payloads, write_plan)
    diagnostics = diagnostics_payload(
      docs: docs,
      write_plan: write_plan,
      elapsed_seconds: elapsed_seconds_since(started_at),
      target_doc_ids: targeted_build? ? target_doc_ids : nil
    )
    print_diagnostics(diagnostics)
    {
      index_payload: index_payload,
      item_payloads: item_payloads,
      reference_payloads: reference_payloads,
      write_plan: write_plan,
      diagnostics: diagnostics
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

  def targeted_build?
    !@only_doc_ids.nil?
  end

  def validate_targeted_build_prerequisites!(docs, target_doc_ids)
    raise "Targeted docs build requires existing scope index; run a full-scope build first" unless @output_dir.join("index.json").file?
    raise "Targeted docs build requires existing references index; run a full-scope build first" unless references_dir.join("index.json").file?

    missing_payload_ids = docs
      .map(&:doc_id)
      .reject { |doc_id| target_doc_ids.include?(doc_id) }
      .reject { |doc_id| @items_dir.join("#{doc_id}.json").file? }
    return if missing_payload_ids.empty?

    raise "Targeted docs build requires existing payloads for unselected docs; run a full-scope build first: #{missing_payload_ids.join(', ')}"
  end

  def load_docs
    all_paths = Dir.glob(@source_dir.join("**/*.md").to_s).sort.map { |file_path| Pathname(file_path) }
    @source_files_scanned = all_paths.length
    nested_paths = all_paths.select { |path| path.dirname != @source_dir }
    if !@allow_nested_source && !nested_paths.empty?
      nested_list = nested_paths.map { |path| path.relative_path_from(@source_dir).to_s }.join(", ")
      raise "Nested markdown docs are not supported under #{@source_dir}; move these files to the scope root: #{nested_list}"
    end

    all_paths.filter_map do |path|
      relative_path = path.relative_path_from(@source_dir).to_s
      front_matter, body_markdown = parse_source(path)

      stem = path.basename(".md").to_s
      doc_id = (front_matter["doc_id"] || stem).to_s
      title = (front_matter["title"] || extract_title(body_markdown) || humanize(stem)).to_s
      parent_id = front_matter.key?("parent_id") ? front_matter["parent_id"].to_s : ""
      last_updated = front_matter["last_updated"] ? front_matter["last_updated"].to_s : ""
      added_date = front_matter["added_date"] ? front_matter["added_date"].to_s : last_updated
      summary = normalize_summary(front_matter["summary"])
      ui_status = normalize_ui_status(front_matter["ui_status"])
      sort_order = normalize_sort_order(front_matter["sort_order"])
      hidden = hidden_front_matter_value(front_matter)
      viewable = !hidden
      viewer_report = normalize_optional_string(front_matter["viewer_report"])
      viewer_report_scope = normalize_optional_string(front_matter["viewer_report_scope"])
      viewer_report_access = normalize_optional_string(front_matter["viewer_report_access"])
      viewer_report_preset = normalize_optional_string(front_matter["viewer_report_preset"])

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
        hidden: hidden,
        viewable: viewable,
        source_path: relative_path,
        viewer_url: viewer_url_for(doc_id),
        content_url: content_url_for(doc_id),
        viewer_report: viewer_report,
        viewer_report_scope: viewer_report_scope,
        viewer_report_access: viewer_report_access,
        viewer_report_preset: viewer_report_preset,
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
  rescue Psych::SyntaxError => error
    raise FrontMatterSyntaxError, front_matter_syntax_error(path, error)
  end

  def front_matter_syntax_error(path, error)
    display_path = begin
      path.relative_path_from(Pathname.pwd).to_s
    rescue ArgumentError
      path.to_s
    end
    location = [
      ("line #{error.line}" if error.respond_to?(:line) && error.line),
      ("column #{error.column}" if error.respond_to?(:column) && error.column)
    ].compact.join(" ")
    detail = error.respond_to?(:problem) && error.problem ? error.problem : error.message
    message = "problem with front-matter on doc #{display_path}"
    message += " at #{location}" unless location.empty?
    "#{message}: #{detail}"
  end

  def boolean_front_matter_value(front_matter, key, default)
    return default unless front_matter.key?(key)

    value = front_matter[key]
    return value if value == true || value == false

    !%w[false 0 no off].include?(value.to_s.strip.downcase)
  end

  def hidden_front_matter_value(front_matter)
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

  def normalize_optional_string(value)
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
    item_payload ||= load_json_file(@items_dir.join("#{doc.doc_id}.json"))
    entry = {
      "scope" => doc.scope_id,
      "doc_id" => doc.doc_id,
      "title" => doc.title,
      "added_date" => doc.added_date,
      "last_updated" => doc.last_updated,
      "parent_id" => effective_parent_id(doc, docs),
      "sort_order" => doc.sort_order,
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
    add_report_metadata(entry, doc)
    entry
  end

  def item_entry(doc, docs, semantic_references_by_doc)
    resolved_markdown = resolve_content_tokens(doc.body_markdown, doc: doc, references_by_doc: semantic_references_by_doc)
    entry = {
      "scope" => doc.scope_id,
      "doc_id" => doc.doc_id,
      "title" => doc.title,
      "added_date" => doc.added_date,
      "last_updated" => doc.last_updated,
      "parent_id" => effective_parent_id(doc, docs),
      "sort_order" => doc.sort_order,
      "hidden" => doc.hidden,
      "viewable" => doc.viewable,
      "source_path" => doc.source_path,
      "viewer_url" => doc.viewer_url,
      "content_html" => add_missing_image_titles(
        rewrite_doc_links(
          JekyllMarkdownRenderer.render_string(resolved_markdown),
          current_doc: doc,
          docs: docs
        )
      )
    }
    entry["summary"] = doc.summary unless doc.summary.empty?
    entry["ui_status"] = doc.ui_status unless doc.ui_status.empty?
    add_report_metadata(entry, doc)
    entry
  end

  def add_report_metadata(entry, doc)
    entry["viewer_report"] = doc.viewer_report unless doc.viewer_report.empty?
    entry["viewer_report_scope"] = doc.viewer_report_scope unless doc.viewer_report_scope.empty?
    entry["viewer_report_access"] = doc.viewer_report_access unless doc.viewer_report_access.empty?
    entry["viewer_report_preset"] = doc.viewer_report_preset unless doc.viewer_report_preset.empty?
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

  def add_missing_image_titles(html)
    html.to_s.gsub(IMG_PATTERN) do
      raw_attrs = Regexp.last_match(1).to_s
      alt = html_attribute(raw_attrs, "alt").to_s.strip
      title = html_attribute(raw_attrs, "title").to_s.strip
      next Regexp.last_match(0) if alt.empty? || !title.empty?

      attrs = raw_attrs.sub(/\s*\/\s*\z/, "")
      closing = raw_attrs.match?(/\s*\/\s*\z/) ? " /" : ""
      %(<img#{attrs} title="#{CGI.escapeHTML(CGI.unescapeHTML(alt))}"#{closing}>)
    end
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

  def build_reference_payloads(docs, semantic_references_by_doc)
    references = docs.flat_map { |doc| semantic_references_by_doc.fetch(doc.doc_id, []) }
    by_doc_payloads = semantic_references_by_doc.each_with_object({}) do |(doc_id, refs), memo|
      next if refs.empty?

      memo[doc_id] = {
        "header" => {
          "schema" => "docs_semantic_references_by_doc_v1",
          "scope" => @scope_id,
          "doc_id" => doc_id,
          "count" => refs.length
        },
        "references" => refs
      }
    end

    by_target = references.group_by { |ref| [ref.fetch("target_kind"), ref.fetch("target_id")] }
    by_target_payloads = by_target.each_with_object({}) do |((target_kind, target_id), refs), memo|
      first = refs.first
      memo[[target_kind, target_id]] = {
        "header" => {
          "schema" => "docs_semantic_references_by_target_v1",
          "scope" => @scope_id,
          "count" => refs.length
        },
        "target_key" => first.fetch("target_key"),
        "target_kind" => target_kind,
        "target_id" => target_id,
        "target_href" => first.fetch("target_href"),
        "target_title" => first.fetch("target_title", ""),
        "target_status" => first.fetch("target_status"),
        "count" => refs.length,
        "references" => refs.map do |ref|
          {
            "source_scope" => ref.fetch("source_scope"),
            "source_doc_id" => ref.fetch("source_doc_id"),
            "source_title" => ref.fetch("source_title"),
            "source_path" => ref.fetch("source_path"),
            "source_viewer_url" => ref.fetch("source_viewer_url"),
            "label" => ref.fetch("label"),
            "action" => ref.fetch("action"),
            "ordinal" => ref.fetch("ordinal")
          }
        end.sort_by { |ref| [ref.fetch("source_title").downcase, ref.fetch("source_doc_id"), ref.fetch("ordinal")] }
      }
    end

    index_targets = by_target_payloads.values.map do |payload|
      target_kind = payload.fetch("target_kind")
      target_id = payload.fetch("target_id")
      {
        "target_key" => payload.fetch("target_key"),
        "target_kind" => target_kind,
        "target_id" => target_id,
        "target_href" => payload.fetch("target_href"),
        "target_title" => payload.fetch("target_title", ""),
        "target_status" => payload.fetch("target_status"),
        "count" => payload.fetch("count"),
        "bucket_url" => reference_target_url(target_kind, target_id)
      }
    end.sort_by { |target| [target.fetch("target_kind"), target.fetch("target_id")] }

    index_without_generated_at = {
      "header" => {
        "schema" => "docs_semantic_references_index_v1",
        "scope" => @scope_id,
        "count" => references.length,
        "target_count" => index_targets.length
      },
      "targets" => index_targets
    }
    {
      index: index_without_generated_at.merge(
        "header" => index_without_generated_at.fetch("header").merge(
          "generated_at" => effective_reference_generated_at(index_without_generated_at)
        )
      ),
      by_doc: by_doc_payloads,
      by_target: by_target_payloads
    }
  end

  def effective_reference_generated_at(index_payload_without_generated_at)
    existing_payload = load_json_file(references_dir.join("index.json"))
    return Time.now.utc.iso8601 unless existing_payload.is_a?(Hash)

    existing_header = existing_payload.fetch("header", {}).dup
    existing_generated_at = existing_header.delete("generated_at").to_s
    comparable_existing = existing_payload.merge("header" => existing_header)
    return Time.now.utc.iso8601 unless comparable_existing == index_payload_without_generated_at
    return Time.now.utc.iso8601 if existing_generated_at.empty?

    existing_generated_at
  end

  def write_outputs(index_payload, item_payloads, reference_payloads, write_plan)
    write_payload_set(@output_dir, @items_dir, index_payload, item_payloads, write_plan)
    write_reference_payload_set(reference_payloads, write_plan)
  end

  def dry_run_summary(index_payload, item_payloads, reference_payloads, write_plan)
    puts "Dry run:"
    puts "  scope: #{@scope_id}"
    puts "  source: #{@source_dir}"
    puts "  docs: #{index_payload.fetch("docs").length}"
    puts "  semantic references: #{reference_payloads.fetch(:index).fetch("header").fetch("count")}"
    puts "  would write index: #{write_plan[:index_write] ? 1 : 0}"
    puts "  would write doc payloads: #{write_plan[:changed_item_ids].length}"
    puts "  would remove stale doc payloads: #{write_plan[:stale_item_ids].length}"
    puts "  would write references index: #{write_plan[:reference_index_write] ? 1 : 0}"
    puts "  would write reference by-doc payloads: #{write_plan[:changed_reference_doc_ids].length}"
    puts "  would write reference by-target payloads: #{write_plan[:changed_reference_target_keys].length}"
    puts "  would remove stale reference by-doc payloads: #{write_plan[:stale_reference_doc_ids].length}"
    puts "  would remove stale reference by-target payloads: #{write_plan[:stale_reference_target_keys].length}"
  end

  def diagnostics_payload(docs:, write_plan:, elapsed_seconds:, target_doc_ids: nil)
    {
      "scope" => @scope_id,
      "build_mode" => target_doc_ids.nil? ? "full" : "targeted",
      "only_doc_ids" => target_doc_ids || [],
      "source_files_scanned" => @source_files_scanned,
      "docs_emitted" => docs.length,
      "doc_payloads_changed" => write_plan[:changed_item_ids].length,
      "doc_payloads_removed" => write_plan[:stale_item_ids].length,
      "reference_index_changed" => write_plan[:reference_index_write] ? 1 : 0,
      "reference_by_doc_payloads_changed" => write_plan[:changed_reference_doc_ids].length,
      "reference_by_doc_payloads_removed" => write_plan[:stale_reference_doc_ids].length,
      "reference_by_target_payloads_changed" => write_plan[:changed_reference_target_keys].length,
      "reference_by_target_payloads_removed" => write_plan[:stale_reference_target_keys].length,
      "warning_count" => @warnings.length,
      "warnings" => @warnings,
      "elapsed_seconds" => elapsed_seconds
    }
  end

  def print_diagnostics(diagnostics)
    puts "Docs builder diagnostics: #{JSON.generate(diagnostics)}"
  end

  def monotonic_time
    Process.clock_gettime(Process::CLOCK_MONOTONIC)
  end

  def elapsed_seconds_since(started_at)
    (monotonic_time - started_at).round(3)
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

  def write_reference_payload_set(reference_payloads, write_plan)
    FileUtils.mkdir_p(references_by_doc_dir)
    FileUtils.mkdir_p(references_by_target_dir)

    index_path = references_dir.join("index.json")
    write_text(index_path, write_plan[:reference_index_text]) if write_plan[:reference_index_write]

    write_plan[:changed_reference_doc_ids].each do |doc_id|
      write_text(references_by_doc_dir.join("#{doc_id}.json"), write_plan[:reference_doc_text_by_id].fetch(doc_id))
    end

    write_plan[:stale_reference_doc_ids].each do |doc_id|
      FileUtils.rm_f(references_by_doc_dir.join("#{doc_id}.json"))
    end

    write_plan[:changed_reference_target_keys].each do |key|
      path = reference_target_path(*key)
      FileUtils.mkdir_p(path.dirname)
      write_text(path, write_plan[:reference_target_text_by_key].fetch(key))
    end

    write_plan[:stale_reference_target_keys].each do |key|
      FileUtils.rm_f(reference_target_path(*key))
    end

    puts "References JSON done for scope #{@scope_id}."
    puts "Reference index wrote: #{write_plan[:reference_index_write] ? 1 : 0}. Path: #{index_path}"
    puts "Reference by-doc payloads wrote: #{write_plan[:changed_reference_doc_ids].length}. Path: #{references_by_doc_dir}"
    puts "Reference by-doc payloads removed: #{write_plan[:stale_reference_doc_ids].length}. Path: #{references_by_doc_dir}"
    puts "Reference by-target payloads wrote: #{write_plan[:changed_reference_target_keys].length}. Path: #{references_by_target_dir}"
    puts "Reference by-target payloads removed: #{write_plan[:stale_reference_target_keys].length}. Path: #{references_by_target_dir}"
  end

  def build_write_plan(index_payload, item_payloads, reference_payloads, target_doc_ids: nil)
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
    reference_plan = build_reference_write_plan(reference_payloads, target_doc_ids: target_doc_ids)
    stale_item_ids = existing_item_ids - desired_item_ids
    stale_item_ids &= target_doc_ids if target_doc_ids

    {
      index_write: existing_index_text != index_text,
      index_text: index_text,
      changed_item_ids: changed_item_ids.sort,
      stale_item_ids: stale_item_ids.sort,
      item_text_by_id: item_text_by_id
    }.merge(reference_plan)
  end

  def build_reference_write_plan(reference_payloads, target_doc_ids: nil)
    reference_index_text = json_text(reference_payloads.fetch(:index))
    changed_doc_ids = []
    doc_text_by_id = {}
    reference_payloads.fetch(:by_doc).each do |doc_id, payload|
      text = json_text(payload)
      doc_text_by_id[doc_id] = text
      changed_doc_ids << doc_id if read_text(references_by_doc_dir.join("#{doc_id}.json")) != text
    end

    changed_target_keys = []
    target_text_by_key = {}
    reference_payloads.fetch(:by_target).each do |key, payload|
      text = json_text(payload)
      target_text_by_key[key] = text
      changed_target_keys << key if read_text(reference_target_path(*key)) != text
    end

    {
      reference_index_write: read_text(references_dir.join("index.json")) != reference_index_text,
      reference_index_text: reference_index_text,
      changed_reference_doc_ids: target_doc_ids ? (changed_doc_ids & target_doc_ids).sort : changed_doc_ids.sort,
      stale_reference_doc_ids: stale_reference_doc_ids(reference_payloads, target_doc_ids),
      reference_doc_text_by_id: doc_text_by_id,
      changed_reference_target_keys: changed_target_keys.sort,
      stale_reference_target_keys: (existing_reference_target_keys - reference_payloads.fetch(:by_target).keys.sort).sort,
      reference_target_text_by_key: target_text_by_key
    }
  end

  def stale_reference_doc_ids(reference_payloads, target_doc_ids)
    stale_ids = existing_reference_doc_ids - reference_payloads.fetch(:by_doc).keys.sort
    stale_ids &= target_doc_ids if target_doc_ids
    stale_ids.sort
  end

  def existing_reference_records_by_doc(docs, target_doc_ids)
    doc_ids = docs.map(&:doc_id) - target_doc_ids
    doc_ids.each_with_object({}) do |doc_id, memo|
      payload = load_json_file(references_by_doc_dir.join("#{doc_id}.json"))
      refs = payload.is_a?(Hash) ? payload["references"] : nil
      memo[doc_id] = refs if refs.is_a?(Array)
    end
  end

  def existing_doc_payload_ids(items_dir)
    return [] unless items_dir.exist?

    Dir.glob(items_dir.join("*.json").to_s).sort.map do |file_path|
      Pathname(file_path).basename(".json").to_s
    end
  end

  def references_dir
    @references_dir ||= @output_dir.join("references")
  end

  def references_by_doc_dir
    @references_by_doc_dir ||= references_dir.join("by-doc")
  end

  def references_by_target_dir
    @references_by_target_dir ||= references_dir.join("by-target")
  end

  def reference_target_path(target_kind, target_id)
    references_by_target_dir.join(target_kind.to_s, "#{reference_target_id_slug(target_id)}.json")
  end

  def reference_target_url(target_kind, target_id)
    "#{@output_url_base}/references/by-target/#{CGI.escape(target_kind.to_s)}/#{reference_target_id_slug(target_id)}.json"
  end

  def reference_target_id_slug(target_id)
    CGI.escape(target_id.to_s)
  end

  def existing_reference_doc_ids
    existing_doc_payload_ids(references_by_doc_dir)
  end

  def existing_reference_target_keys
    return [] unless references_by_target_dir.exist?

    Dir.glob(references_by_target_dir.join("*", "*.json").to_s).sort.map do |file_path|
      path = Pathname(file_path)
      [
        path.dirname.basename.to_s,
        CGI.unescape(path.basename(".json").to_s)
      ]
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
    raise "Docs output path must be inside the repo root: #{output_dir}" if relative_path == ".." || relative_path.start_with?("../")

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

  def resolve_interactive_html_tokens(markdown)
    return markdown unless markdown.include?("[[interactive-html:")

    markdown.gsub(INTERACTIVE_HTML_TOKEN_PATTERN) do
      interactive_html_iframe(Regexp.last_match(1))
    end
  end

  def resolve_content_tokens(markdown, doc:, references_by_doc:)
    resolved = resolve_interactive_html_tokens(resolve_media_tokens(markdown))
    resolve_semantic_ref_tokens(resolved, doc: doc, references_by_doc: references_by_doc)
  end

  def interactive_html_iframe(raw_token_body)
    token = parse_interactive_html_token(raw_token_body)
    filename = token.fetch(:filename)
    asset_path = interactive_html_asset_path(filename)
    raise "Interactive HTML asset not found for scope #{@scope_id}: #{interactive_html_asset_relative_path(filename)}" unless asset_path.file?

    public_path = "/assets/docs/interactive/#{@scope_id}/#{filename}"
    title = "Interactive HTML: #{filename}"
    style_attr = token[:height] ? %( style="--docs-viewer-interactive-height: #{token[:height]}px") : ""
    <<~HTML.chomp
      <iframe class="docsViewer__interactiveFrame" src="#{CGI.escapeHTML(public_path)}" sandbox="allow-scripts" loading="lazy" title="#{CGI.escapeHTML(title)}"#{style_attr}></iframe>
    HTML
  end

  def parse_interactive_html_token(raw_token_body)
    parts = raw_token_body.to_s.strip.split(/\s+/)
    filename = normalize_interactive_html_filename(parts.shift)
    token = { filename: filename }
    parts.each do |part|
      key, value = part.split("=", 2)
      case key
      when "height"
        token[:height] = normalize_interactive_html_height(value, raw_token_body)
      else
        raise "Invalid interactive HTML token attribute #{part.inspect}; supported attributes: height"
      end
    end
    token
  end

  def normalize_interactive_html_filename(raw_filename)
    filename = raw_filename.to_s.strip
    unless filename.match?(INTERACTIVE_HTML_FILENAME_PATTERN)
      raise "Invalid interactive HTML token #{raw_filename.inspect}; use a same-scope .html filename only"
    end
    filename
  end

  def normalize_interactive_html_height(raw_height, raw_token_body)
    height = raw_height.to_s.strip
    unless height.match?(INTERACTIVE_HTML_HEIGHT_PATTERN)
      raise "Invalid interactive HTML token height in #{raw_token_body.inspect}; use height=<positive pixel integer>"
    end
    height.to_i
  end

  def interactive_html_asset_relative_path(filename)
    Pathname("assets/docs/interactive").join(@scope_id, filename).to_s
  end

  def interactive_html_asset_path(filename)
    @repo_root.join(interactive_html_asset_relative_path(filename)).cleanpath
  end

  def resolve_semantic_ref_tokens(markdown, doc:, references_by_doc:)
    return markdown unless markdown.include?("[[ref:")

    references = []
    ordinal = 0
    rendered = replace_semantic_ref_tokens_outside_code(markdown) do |raw_token, raw_body, raw_modifier|
      ordinal += 1
      token = parse_semantic_ref_token(raw_token, raw_body, raw_modifier)
      if token.nil?
        warn_semantic_ref(doc, "malformed semantic reference token #{raw_token.inspect}")
        next %(<span data-ref-status="malformed">#{CGI.escapeHTML(raw_token)}</span>)
      end

      resolution = resolve_semantic_ref(token)
      warnings = semantic_ref_warnings(token, resolution)
      warnings.each { |message| warn_semantic_ref(doc, message) }
      references << semantic_ref_record(doc, token, resolution, ordinal)
      render_semantic_ref_token(token, resolution, warnings.empty?)
    end

    references_by_doc[doc.doc_id] = references
    rendered
  end

  def replace_semantic_ref_tokens_outside_code(markdown)
    output = +""
    in_fence = false
    fence_marker = nil
    markdown.each_line do |line|
      fence_match = line.match(/\A {0,3}(`{3,}|~{3,})/)
      if fence_match
        marker = fence_match[1]
        if in_fence && marker.start_with?(fence_marker)
          in_fence = false
          fence_marker = nil
        elsif !in_fence
          in_fence = true
          fence_marker = marker[0]
        end
        output << line
        next
      end

      output << (in_fence ? line : replace_semantic_ref_tokens_outside_inline_code(line) { |*args| yield(*args) })
    end
    output
  end

  def replace_semantic_ref_tokens_outside_inline_code(line)
    output = +""
    index = 0
    while index < line.length
      tick_match = line.match(/`+/, index)
      segment_end = tick_match ? tick_match.begin(0) : line.length
      output << replace_semantic_ref_tokens_in_text(line[index...segment_end]) { |*args| yield(*args) }
      break unless tick_match

      tick = tick_match[0]
      close_index = line.index(tick, tick_match.end(0))
      if close_index
        output << line[tick_match.begin(0)...close_index + tick.length]
        index = close_index + tick.length
      else
        output << line[tick_match.begin(0)..]
        index = line.length
      end
    end
    output
  end

  def replace_semantic_ref_tokens_in_text(text)
    text.gsub(SEMANTIC_REF_TOKEN_PATTERN) do
      yield(Regexp.last_match(0), Regexp.last_match(1), Regexp.last_match(2))
    end
  end

  def parse_semantic_ref_token(raw_token, raw_body, raw_modifier)
    body = raw_body.to_s
    target, explicit_label = body.split("|", 2)
    kind, id = target.to_s.split(":", 2)
    kind = kind.to_s.strip.downcase
    id = id.to_s.strip
    return nil if kind.empty? || id.empty?
    return nil unless kind.match?(/\A[a-z0-9_-]+\z/)

    modifier = parse_semantic_ref_modifier(raw_modifier)
    SemanticRefToken.new(
      raw: raw_token,
      kind: kind,
      id: id,
      label: explicit_label&.strip,
      action: modifier.fetch(:action, "link"),
      modifier_error: modifier[:error]
    )
  end

  def parse_semantic_ref_modifier(raw_modifier)
    return { action: "link" } if raw_modifier.to_s.strip.empty?

    inner = raw_modifier.to_s.strip.sub(/\A\{/, "").sub(/\}\z/, "").strip
    return { action: "link", error: "empty modifier" } if inner.empty?

    attrs = {}
    inner.split(/\s+/).each do |part|
      key, value = part.split("=", 2)
      return { action: "link", error: "invalid modifier #{part.inspect}" } if key.to_s.empty? || value.to_s.empty?

      attrs[key] = value
    end
    unsupported = attrs.keys - ["action"]
    return { action: attrs.fetch("action", "link"), error: "unsupported modifier #{unsupported.first.inspect}" } unless unsupported.empty?

    { action: attrs.fetch("action", "link") }
  end

  def resolve_semantic_ref(token)
    return unsupported_semantic_ref_resolution(token) unless SEMANTIC_REF_SUPPORTED_KINDS.include?(token.kind)

    case token.kind
    when "work"
      resolve_catalogue_ref(token, catalogue_work_records, "work_id", 5, "/works")
    when "series"
      resolve_catalogue_ref(token, catalogue_series_records, "series_id", 3, "/series", allow_slug_id: true)
    when "moment"
      resolve_catalogue_ref(token, catalogue_moment_records, "moment_id", nil, "/moments", moment_id: true)
    end
  end

  def unsupported_semantic_ref_resolution(token)
    {
      target_kind: token.kind,
      target_id: token.id,
      target_key: "#{token.kind}:#{token.id}",
      target_href: "",
      target_title: "",
      target_status: "unsupported_kind",
      exists: false,
      linkable: false,
      warning: "unsupported semantic reference kind #{token.kind.inspect}"
    }
  end

  def resolve_catalogue_ref(token, records, id_field, numeric_width, route_base, allow_slug_id: false, moment_id: false)
    normalized_id = if moment_id
      normalize_moment_id(token.id)
    elsif allow_slug_id
      normalize_semantic_series_id(token.id, numeric_width)
    else
      normalize_numeric_semantic_id(token.id, numeric_width)
    end
    record = records[normalized_id]
    target_key = "#{token.kind}:#{normalized_id}"
    unless record
      return {
        target_kind: token.kind,
        target_id: normalized_id,
        target_key: target_key,
        target_href: "",
        target_title: "",
        target_status: "missing",
        exists: false,
        linkable: false,
        warning: "unresolved semantic reference #{target_key}"
      }
    end

    status = record.fetch("status", "").to_s.strip.downcase
    href = "#{route_base}/#{CGI.escape(normalized_id)}/"
    {
      target_kind: token.kind,
      target_id: record.fetch(id_field, normalized_id).to_s,
      target_key: target_key,
      target_href: href,
      target_title: record.fetch("title", "").to_s.strip,
      target_status: status.empty? ? "unknown" : status,
      exists: true,
      linkable: status == "published",
      warning: status == "published" ? "" : "semantic reference #{target_key} targets non-published catalogue record"
    }
  rescue ArgumentError
    {
      target_kind: token.kind,
      target_id: token.id,
      target_key: "#{token.kind}:#{token.id}",
      target_href: "",
      target_title: "",
      target_status: "invalid_id",
      exists: false,
      linkable: false,
      warning: "invalid semantic reference id #{token.kind}:#{token.id}"
    }
  end

  def normalize_numeric_semantic_id(value, width)
    text = value.to_s.strip.sub(/\A'/, "").sub(/\.0+\z/, "").gsub(/\D/, "")
    raise ArgumentError, "invalid id" if text.empty?

    text.rjust(width, "0")
  end

  def normalize_semantic_series_id(value, width)
    text = value.to_s.strip.sub(/\A'/, "").sub(/\.0+\z/, "")
    raise ArgumentError, "invalid series id" if text.empty?

    return text.rjust(width, "0") if text.match?(/\A\d+\z/)
    return text if text.match?(/\A[a-z0-9]+(?:-[a-z0-9]+)*\z/)

    raise ArgumentError, "invalid series id"
  end

  def normalize_moment_id(value)
    text = value.to_s.strip.downcase
    text = text.delete_suffix(".md")
    raise ArgumentError, "invalid moment id" unless text.match?(/\A[a-z0-9]+(?:-[a-z0-9]+)*\z/)

    text
  end

  def semantic_ref_warnings(token, resolution)
    warnings = []
    warnings << token.modifier_error if token.modifier_error.to_s != ""
    warnings << "unsupported semantic reference action #{token.action.inspect}" unless SEMANTIC_REF_ALLOWED_ACTIONS.include?(token.action)
    warnings << resolution[:warning] if resolution[:warning].to_s != ""
    warnings
  end

  def warn_semantic_ref(doc, message)
    warning = "Docs semantic reference warning [#{@scope_id}/#{doc.doc_id}]: #{message}"
    @warnings << warning
    warn warning
  end

  def semantic_ref_record(doc, token, resolution, ordinal)
    label = semantic_ref_label(token, resolution)
    {
      "source_scope" => @scope_id,
      "source_doc_id" => doc.doc_id,
      "source_title" => doc.title,
      "source_path" => doc.source_path,
      "source_viewer_url" => doc.viewer_url,
      "target_kind" => resolution[:target_kind],
      "target_id" => resolution[:target_id],
      "target_key" => resolution[:target_key],
      "target_href" => resolution[:target_href],
      "target_title" => resolution[:target_title],
      "target_status" => resolution[:target_status],
      "label" => label,
      "action" => token.action,
      "ordinal" => ordinal
    }
  end

  def semantic_ref_label(token, resolution)
    explicit_label = token.label.to_s.strip
    return explicit_label unless explicit_label.empty?

    title = resolution[:target_title].to_s.strip
    title.empty? ? resolution[:target_key].to_s : title
  end

  def render_semantic_ref_token(token, resolution, usable)
    label = CGI.escapeHTML(semantic_ref_label(token, resolution))
    attrs = {
      "data-ref-kind" => resolution[:target_kind],
      "data-ref-id" => resolution[:target_id],
      "data-ref-action" => token.action
    }
    if usable && resolution[:linkable] && !resolution[:target_href].to_s.empty?
      attrs["target"] = "_blank"
      attrs["rel"] = "noopener noreferrer"
      return %(<a href="#{CGI.escapeHTML(resolution[:target_href])}" #{html_attrs(attrs)}>#{label}</a>)
    end

    attrs["data-ref-status"] = resolution[:target_status]
    %(<span #{html_attrs(attrs)}>#{label}</span>)
  end

  def html_attrs(attrs)
    attrs.map do |key, value|
      %(#{key}="#{CGI.escapeHTML(value.to_s)}")
    end.join(" ")
  end

  def catalogue_work_records
    @catalogue_work_records ||= load_catalogue_records("works.json", "works", "work_id")
  end

  def catalogue_series_records
    @catalogue_series_records ||= load_catalogue_records("series.json", "series", "series_id")
  end

  def catalogue_moment_records
    @catalogue_moment_records ||= load_catalogue_records("moments.json", "moments", "moment_id")
  end

  def load_catalogue_records(filename, root_key, id_field)
    path = @repo_root.join("studio/data/canonical/catalogue/#{filename}")
    payload = JSON.parse(path.read)
    records = payload[root_key]
    pairs = records.is_a?(Hash) ? records.values : Array(records)
    pairs.each_with_object({}) do |record, memo|
      next unless record.is_a?(Hash)

      id = record[id_field].to_s.strip
      memo[id] = record unless id.empty?
    end
  rescue Errno::ENOENT, JSON::ParserError
    {}
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
  "/#{config.search_output.sub(%r{\A/+}, "")}"
end

def path_under?(path, root)
  normalized_path = path.to_s.sub(%r{\A/+}, "")
  normalized_root = root.to_s.sub(%r{\A/+}, "").sub(%r{/+\z}, "")
  normalized_path == normalized_root || normalized_path.start_with?("#{normalized_root}/")
end

def manage_mode_scope_config?(config)
  config.include_scope_param == true || normalized_browser_viewer_base_url(config.viewer_base_url) == DOCS_VIEWER_MANAGE_ROUTE_BASE_URL
end

def validate_generated_output_contract!(config, index)
  return unless manage_mode_scope_config?(config)

  if path_under?(config.output, "assets/data/docs/scopes")
    raise "Docs scope config scopes[#{index}].output for manage-mode scope #{config.scope_id.inspect} must not be under assets/data/docs/scopes"
  end
  if path_under?(config.search_output, "assets/data/search")
    raise "Docs scope config scopes[#{index}].search_output for manage-mode scope #{config.scope_id.inspect} must not be under assets/data/search"
  end
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

def docs_viewer_settings_payload(scope_configs)
  docs_scope_payload = JSON.parse(File.read(DOCS_SCOPE_CONFIG_PATH))
  docs_viewer_settings = docs_scope_payload["docs_viewer"]
  return nil unless docs_viewer_settings.is_a?(Hash)

  settings = JSON.parse(JSON.generate(docs_viewer_settings))
  statuses_by_scope = settings["ui_statuses_by_scope"]
  if statuses_by_scope.is_a?(Hash)
    scope_ids = scope_configs.map(&:scope_id)
    settings["ui_statuses_by_scope"] = statuses_by_scope.select { |scope_id, _value| scope_ids.include?(scope_id) }
  end
  settings
end

def browser_scope_config_payload(scope_configs)
  payload = {
    "schema_version" => DOCS_VIEWER_BROWSER_CONFIG_SCHEMA_VERSION,
    "default_scope_id" => scope_configs.first&.scope_id.to_s,
    "scopes" => scope_configs.map do |config|
      {
        "scope_id" => config.scope_id,
        "scope_type" => config.scope_type,
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
  docs_viewer_settings = docs_viewer_settings_payload(scope_configs)
  payload["docs_viewer"] = docs_viewer_settings if docs_viewer_settings
  payload
end

def write_docs_viewer_browser_config(scope_configs, path: DOCS_VIEWER_BROWSER_CONFIG_PATH, label: "Docs Viewer browser config")
  payload = browser_scope_config_payload(scope_configs)
  text = JSON.pretty_generate(payload) + "\n"
  FileUtils.mkdir_p(File.dirname(path))
  if File.exist?(path) && File.read(path) == text
    puts "#{label} unchanged: #{path}"
    return
  end
  File.write(path, text)
  puts "#{label} wrote: #{path}"
end

def public_readonly_scope_config?(config)
  !config.include_scope_param && normalized_browser_viewer_base_url(config.viewer_base_url) != DOCS_VIEWER_MANAGE_ROUTE_BASE_URL
end

def write_docs_viewer_public_browser_config(scope_configs)
  write_docs_viewer_browser_config(
    scope_configs.select { |config| public_readonly_scope_config?(config) },
    path: DOCS_VIEWER_PUBLIC_BROWSER_CONFIG_PATH,
    label: "Docs Viewer public browser config"
  )
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
    config = ScopeConfig.new(
      scope_id: scope_id,
      scope_type: item["scope_type"].to_s.strip.downcase,
      source: normalize_scope_config_path(item["source"], "scopes[#{index}].source"),
      media_path_prefix: normalize_scope_config_path(
        item["media_path_prefix"] || "docs/#{scope_id}",
        "scopes[#{index}].media_path_prefix"
      ),
      output: normalize_scope_config_path(item["output"], "scopes[#{index}].output"),
      search_output: normalize_scope_config_path(
        item["search_output"],
        "scopes[#{index}].search_output"
      ),
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
    validate_generated_output_contract!(config, index)
    config
  end
end

options = {
  scopes: [],
  source: nil,
  output: nil,
  viewer_base_url: nil,
  write: false,
  only_doc_ids: nil
}

OptionParser.new do |parser|
  parser.banner = "Usage: ./docs-viewer/build/build_docs.rb [options]"

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

  parser.on("--only-doc-ids IDS", "Comma-separated doc ids for a targeted docs payload rebuild") do |value|
    options[:only_doc_ids] = value.to_s.split(",").map(&:strip).reject(&:empty?)
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

if !options[:only_doc_ids].nil? && selected_scopes.length != 1
  raise "--only-doc-ids can only be used when exactly one scope is selected"
end

if options[:write]
  write_docs_viewer_browser_config(scope_configs)
  write_docs_viewer_public_browser_config(scope_configs)
end

begin
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
      allow_unresolved_parent_ids: config.allow_unresolved_parent_ids,
      only_doc_ids: options[:only_doc_ids]
    )
    builder.run(write: options[:write])
  end
rescue FrontMatterSyntaxError => error
  warn error.message
  exit 1
end
