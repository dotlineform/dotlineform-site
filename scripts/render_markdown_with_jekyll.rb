#!/usr/bin/env ruby
# frozen_string_literal: true

require_relative "jekyll_markdown_renderer"

if ARGV.length != 1
  warn "Usage: render_markdown_with_jekyll.rb <markdown-path>"
  exit 1
end

source_path = Pathname(ARGV[0]).expand_path
unless source_path.file?
  warn "Source markdown not found: #{source_path}"
  exit 1
end

print JekyllMarkdownRenderer.render_file(source_path)
