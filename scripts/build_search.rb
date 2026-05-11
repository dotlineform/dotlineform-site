#!/usr/bin/env ruby
# frozen_string_literal: true

require "json"
require "pathname"

REPO_ROOT = Pathname(__dir__).parent.realpath
ADAPTER_REGISTRY_PATH = REPO_ROOT.join("scripts/search/adapter_registry.json")

def normalize_scope(value)
  String(value || "").strip.downcase
end

def requested_scope(argv, default_scope)
  argv.each_with_index do |arg, index|
    if arg == "--scope"
      return normalize_scope(argv[index + 1])
    end

    next unless arg.start_with?("--scope=")

    return normalize_scope(arg.split("=", 2).last)
  end

  normalize_scope(default_scope)
end

def load_adapter_registry
  payload = JSON.parse(File.read(ADAPTER_REGISTRY_PATH, encoding: "utf-8"))
  unless payload.is_a?(Hash) && payload["schema_version"] == "search_adapter_registry_v1"
    raise SystemExit, "Invalid search adapter registry: expected search_adapter_registry_v1"
  end

  payload
rescue JSON::ParserError => e
  raise SystemExit, "Failed to parse search adapter registry: #{e.message}"
end

def docs_viewer_scope_ids(scope_config_path)
  payload = JSON.parse(File.read(REPO_ROOT.join(scope_config_path), encoding: "utf-8"))
  scopes = payload.is_a?(Hash) ? payload["scopes"] : nil
  unless scopes.is_a?(Array)
    raise SystemExit, "Invalid Docs Viewer scope config: expected scopes array"
  end

  scopes.filter_map do |item|
    next unless item.is_a?(Hash)

    scope_id = normalize_scope(item["scope_id"])
    scope_id unless scope_id.empty?
  end
rescue JSON::ParserError => e
  raise SystemExit, "Failed to parse Docs Viewer scope config: #{e.message}"
end

registry = load_adapter_registry
scope = requested_scope(ARGV, registry["default_scope"])
static_scopes = registry.fetch("scopes", {})
adapter = static_scopes[scope]

unless adapter
  docs_viewer = registry.fetch("docs_viewer", {})
  docs_scopes = docs_viewer_scope_ids(docs_viewer.fetch("scope_config"))
  adapter = docs_viewer if docs_scopes.include?(scope)
end

unless adapter.is_a?(Hash)
  docs_viewer = registry.fetch("docs_viewer", {})
  docs_scopes = docs_viewer_scope_ids(docs_viewer.fetch("scope_config"))
  known_scopes = (static_scopes.keys + docs_scopes).sort
  raise SystemExit, "Unsupported search scope: #{scope}. Current scopes: #{known_scopes.join(', ')}"
end

script_path = String(adapter["script"] || "").strip
if script_path.empty? || script_path.start_with?("/") || script_path.split("/").include?("..")
  raise SystemExit, "Invalid search adapter script path"
end

load REPO_ROOT.join(script_path).to_s
