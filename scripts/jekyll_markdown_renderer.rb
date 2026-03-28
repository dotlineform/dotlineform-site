#!/usr/bin/env ruby
# frozen_string_literal: true

require "jekyll"
require "pathname"

module JekyllMarkdownRenderer
  module_function

  def repo_root
    @repo_root ||= Pathname(__dir__).parent.realpath
  end

  def site
    @site ||= begin
      Jekyll.logger.log_level = :error
      Jekyll::Site.new(
        Jekyll.configuration(
          "source" => repo_root.to_s,
          "destination" => repo_root.join("_site").to_s,
          "quiet" => true
        )
      )
    end
  end

  def converter
    @converter ||= site.find_converter_instance(Jekyll::Converters::Markdown)
  end

  def render_string(markdown)
    active_converter = converter
    raise "Could not initialize Jekyll markdown converter" if active_converter.nil?

    active_converter.convert(markdown.to_s)
  end

  def render_file(path)
    render_string(Pathname(path).read)
  end
end
