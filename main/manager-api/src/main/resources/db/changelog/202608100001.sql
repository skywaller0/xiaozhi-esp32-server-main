-- 扩展 OpenAI 兼容模型的可配置字段。
-- 本迁移只更新表单元数据，不覆盖用户已经保存的模型配置和密钥。
UPDATE `ai_model_provider`
SET `fields` = '[{"key":"model_name","label":"模型名称","type":"string"},{"key":"base_url","label":"服务地址","type":"string"},{"key":"timeout","label":"请求超时（秒）","type":"number"},{"key":"temperature","label":"温度","type":"number"},{"key":"max_tokens","label":"最大令牌数","type":"number"},{"key":"disable_thinking","label":"关闭思考内容输出","type":"boolean"}]',
    `name` = 'Ollama 本地模型'
WHERE `id` = 'SYSTEM_LLM_ollama';

UPDATE `ai_model_provider`
SET `fields` = '[{"key":"base_url","label":"基础URL","type":"string"},{"key":"model_name","label":"模型名称","type":"string"},{"key":"api_key","label":"API密钥","type":"password"},{"key":"timeout","label":"请求超时（秒）","type":"number"},{"key":"temperature","label":"温度","type":"number"},{"key":"max_tokens","label":"最大令牌数","type":"number"},{"key":"top_p","label":"Top P","type":"number"},{"key":"frequency_penalty","label":"频率惩罚","type":"number"}]',
    `name` = 'OpenAI 兼容接口'
WHERE `id` = 'SYSTEM_LLM_openai';
