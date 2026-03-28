#!/usr/bin/env ruby
# frozen_string_literal: true

require "pathname"
require "jekyll"

if ARGV.length != 1
  warn "Usage: render_markdown_with_jekyll.rb <markdown-path>"
  exit 1
end

source_path = Pathname(ARGV[0]).expand_path
unless source_path.file?
  warn "Source markdown not found: #{source_path}"
  exit 1
end

repo_root = Pathname(__dir__).parent.realpath
Jekyll.logger.log_level = :error

site = Jekyll::Site.new(
  Jekyll.configuration(
    "source" => repo_root.to_s,
    "destination" => repo_root.join("_site").to_s,
    "quiet" => true
  )
)
converter = site.find_converter_instance(Jekyll::Converters::Markdown)
if converter.nil?
  warn "Could not initialize Jekyll markdown converter"
  exit 1
end

print converter.convert(source_path.read)
