package xiaozhi.modules.model.validation;

import java.net.URI;
import java.net.URISyntaxException;
import java.util.Locale;

import org.apache.commons.lang3.StringUtils;
import org.springframework.stereotype.Component;

import cn.hutool.json.JSONObject;
import xiaozhi.common.exception.ErrorCode;
import xiaozhi.common.exception.RenException;
import xiaozhi.common.utils.SensitiveDataUtils;
import xiaozhi.modules.model.dto.ModelConfigBodyDTO;

/**
 * 模型配置领域校验器。
 *
 * <p>控制器只负责 HTTP 参数绑定，服务类负责业务编排，供应器相关的字段校验和规范化统一放在
 * 本类中，避免新增模型入口时在多个控制器中重复实现。</p>
 */
@Component
public class ModelConfigValidator {

    private static final int MAX_TIMEOUT_SECONDS = 600;

    /**
     * 校验并规范化模型配置。该方法会对 DTO 中的 configJson 做受控修改。
     *
     * @param modelType 模型类型，例如 LLM、ASR
     * @param providerCode 供应器编码，例如 openai、ollama
     * @param body 待保存的配置
     * @param creating 是否为新增操作
     */
    public void validateAndNormalize(String modelType, String providerCode,
            ModelConfigBodyDTO body, boolean creating) {
        if (StringUtils.isBlank(body.getModelName())) {
            throw new RenException(ErrorCode.MODEL_CONFIG_NAME_EMPTY);
        }
        if (body.getConfigJson() == null) {
            throw new RenException(ErrorCode.MODEL_CONFIG_JSON_EMPTY);
        }

        if (!"LLM".equalsIgnoreCase(modelType)) {
            return;
        }

        String provider = StringUtils.trimToEmpty(providerCode).toLowerCase(Locale.ROOT);
        JSONObject config = body.getConfigJson();
        // 其他供应器的 type 可能用于 Python 动态模块加载并区分大小写，不能统一改写。
        if (!"openai".equals(provider) && !"ollama".equals(provider)) {
            return;
        }

        validateProviderType(config, provider);
        config.set("type", provider);

        String remoteModelName = getTrimmedString(config, "model_name");
        if (StringUtils.isBlank(remoteModelName)) {
            throw new RenException(ErrorCode.MODEL_REMOTE_NAME_EMPTY);
        }
        config.set("model_name", remoteModelName);
        config.set("base_url", normalizeHttpUrl(getTrimmedString(config, "base_url")));
        normalizeTimeout(config);

        if ("openai".equals(provider)) {
            String apiKey = getTrimmedString(config, "api_key");
            // 编辑时前端会回传掩码；掩码值由服务层保留原密钥，不应在此判空。
            if (StringUtils.isBlank(apiKey) && creating) {
                throw new RenException(ErrorCode.MODEL_API_KEY_EMPTY);
            }
            if (StringUtils.isNotBlank(apiKey) && !SensitiveDataUtils.isMaskedValue(apiKey)) {
                config.set("api_key", apiKey);
            }
        }
    }

    private void validateProviderType(JSONObject config, String provider) {
        String configuredType = getTrimmedString(config, "type").toLowerCase(Locale.ROOT);
        if (StringUtils.isNotBlank(configuredType) && !configuredType.equals(provider)) {
            throw new RenException(ErrorCode.MODEL_PROVIDER_TYPE_MISMATCH);
        }
    }

    private String normalizeHttpUrl(String rawUrl) {
        if (StringUtils.isBlank(rawUrl)) {
            throw new RenException(ErrorCode.MODEL_ENDPOINT_URL_INVALID);
        }

        try {
            URI uri = new URI(rawUrl.trim());
            String scheme = uri.getScheme() == null ? "" : uri.getScheme().toLowerCase(Locale.ROOT);
            if (!("http".equals(scheme) || "https".equals(scheme))
                    || StringUtils.isBlank(uri.getHost())
                    || uri.getUserInfo() != null
                    || uri.getFragment() != null) {
                throw new RenException(ErrorCode.MODEL_ENDPOINT_URL_INVALID);
            }

            String normalized = uri.normalize().toString();
            while (normalized.endsWith("/")) {
                normalized = normalized.substring(0, normalized.length() - 1);
            }
            return normalized;
        } catch (URISyntaxException ex) {
            throw new RenException(ErrorCode.MODEL_ENDPOINT_URL_INVALID, ex);
        }
    }

    private void normalizeTimeout(JSONObject config) {
        Object rawTimeout = config.get("timeout");
        if (rawTimeout == null || StringUtils.isBlank(rawTimeout.toString())) {
            return;
        }

        // OpenAI 适配器兼容 connect/read/write/pool 的细粒度超时对象。
        if (rawTimeout instanceof JSONObject) {
            JSONObject timeoutConfig = (JSONObject) rawTimeout;
            for (String key : new String[] { "connect", "read", "write", "pool" }) {
                Object value = timeoutConfig.get(key);
                if (value != null) {
                    validateTimeoutNumber(value);
                }
            }
            return;
        }

        config.set("timeout", validateTimeoutNumber(rawTimeout));
    }

    private int validateTimeoutNumber(Object rawValue) {
        try {
            int timeout = Integer.parseInt(rawValue.toString());
            if (timeout <= 0 || timeout > MAX_TIMEOUT_SECONDS) {
                throw new RenException(ErrorCode.MODEL_TIMEOUT_INVALID);
            }
            return timeout;
        } catch (NumberFormatException ex) {
            throw new RenException(ErrorCode.MODEL_TIMEOUT_INVALID, ex);
        }
    }

    private String getTrimmedString(JSONObject config, String key) {
        Object value = config.get(key);
        return value == null ? "" : value.toString().trim();
    }
}
