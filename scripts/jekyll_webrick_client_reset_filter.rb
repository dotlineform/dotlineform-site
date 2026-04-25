# frozen_string_literal: true

# Local-dev noise filter for Jekyll's WEBrick server.
#
# Browsers can close sockets during local rebuilds, refreshes, or cancelled asset
# loads. WEBrick reports that as Errno::ECONNRESET at error level even though it
# is usually just "client went away" noise for this repo's dev server.

require "webrick"

module Dotlineform
  module JekyllWEBrickClientResetFilter
    def error(arg)
      return if arg.is_a?(Errno::ECONNRESET)

      super
    end
  end
end

unless WEBrick::Log.ancestors.include?(Dotlineform::JekyllWEBrickClientResetFilter)
  WEBrick::Log.prepend(Dotlineform::JekyllWEBrickClientResetFilter)
end
