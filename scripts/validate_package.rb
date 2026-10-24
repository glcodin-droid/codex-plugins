#!/usr/bin/env ruby
# Structural checks for this repository's installable plugin packages.
require 'json'
require 'yaml'
require 'pathname'

def check(condition, message)
  raise message unless condition
end

root = File.expand_path('..', __dir__)
market = JSON.parse(File.read(File.join(root, '.agents/plugins/marketplace.json')))
check(market['plugins'].is_a?(Array) && !market['plugins'].empty?, '市场插件列表不能为空')
names = market['plugins'].map { |entry| entry['name'] }
check(names.uniq == names, '市场插件名称必须唯一')

market['plugins'].each do |entry|
  dir = File.expand_path(entry.fetch('source').fetch('path'), root)
  check(dir.start_with?(root + '/'), '插件路径必须位于仓库内')
  portable = JSON.parse(File.read(File.join(dir, 'plugin.json')))
  legacy = JSON.parse(File.read(File.join(dir, '.codex-plugin/plugin.json')))
  check(portable['$schema'] == 'https://agent-plugins.org/schemas/1.0.0/plugin.schema.json', '根清单 schema 错误')
  check(portable['name'] == entry['name'], '市场名称与插件名称不一致')
  check(portable['name'].match?(/\A[a-z0-9]+(?:[.-][a-z0-9]+)*\z/), '插件名称无效')
  check(portable['name'].length <= 64, '插件名称过长')
  check(portable['version'].match?(/\A\d+\.\d+\.\d+\z/), '版本必须使用 SemVer')
  %w[name version description author repository license].each do |key|
    check(portable[key] == legacy[key], "兼容清单字段不一致：#{key}")
  end
  interface = portable.fetch('extensions').fetch('com.openai').fetch('interface')
  check(interface == legacy['interface'], '展示信息不一致')
  check(interface['shortDescription'].length <= 30, '插件短描述超过 30 字符')
  check(interface['category'] == 'Productivity', '分类不正确')
  check(legacy['skills'] == './skills/', '兼容清单的技能路径不正确')
  check(%w[skills mcpServers apps interface].none? { |key| portable.key?(key) }, '根清单包含兼容格式字段')
  %w[logo composerIcon].each do |key|
    file = File.expand_path(interface.fetch(key), dir)
    check(file.start_with?(dir + '/') && File.file?(file), "图标不存在或路径越界：#{key}")
  end
  skill_files = Dir.glob(File.join(dir, 'skills/*/SKILL.md'))
  check(!skill_files.empty?, '至少需要一个技能')
  skill_files.each do |file|
    content = File.read(file, encoding: 'UTF-8')
    match = content.match(/\A---\r?\n(.*?)\r?\n---(?:\r?\n|\z)/m)
    check(match, '技能缺少 YAML frontmatter')
    metadata = YAML.safe_load(match[1])
    %w[name description].each { |key| check(metadata[key].is_a?(String) && !metadata[key].strip.empty?, "技能缺少 #{key}") }
    check(File.basename(File.dirname(file)) == metadata['name'], '技能目录与名称不匹配')
    agent = YAML.safe_load(File.read(File.join(File.dirname(file), 'agents/openai.yaml')))
    check(agent['policy']['allow_implicit_invocation'] == true, '隐式调用配置无效')
    check(agent['policy']['products'] == ['CODEX'], '产品范围应为 CODEX')
    %w[display_name short_description].each { |key| check(!agent['interface'][key].strip.empty?, "技能界面缺少 #{key}") }
  end
  puts "PASS #{portable['name']} #{portable['version']}：#{skill_files.length} 个技能，JSON/YAML、路径及兼容清单检查通过"
end
