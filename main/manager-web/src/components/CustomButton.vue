<template>
  <el-button
    :class="['custom-button', `custom-button--${type}`]"
    v-bind="$attrs"
    @click="$emit('click', $event)"
  >
    <slot />
  </el-button>
</template>

<script>
export default {
  name: 'CustomButton',
  props: {
    type: {
      type: String,
      default: 'default',
      validator: (value) => ['default', 'confirm', 'delete', 'add'].includes(value)
    }
  }
};
</script>

<style lang="scss" scoped>
.custom-button {
  width: fit-content;
  min-height: 36px;
  padding: 9px 15px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 650;
  transition: transform 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;

  &:not(.is-disabled):hover {
    transform: translateY(-1px);
  }

  &.el-button--small {
    min-height: 32px;
    padding: 7px 12px;
    font-size: 12px;
  }
}

.custom-button--default {
  border: 1px solid var(--app-border);
  color: var(--app-text);
  background: #fff;

  &:hover {
    border-color: #cbd1dc;
    color: var(--app-text);
    background: #f8f9fb;
  }
}

.custom-button--confirm {
  border-color: var(--app-primary);
  color: #fff;
  background: var(--app-primary);
  box-shadow: 0 5px 12px rgba(70, 87, 232, 0.18);

  &:hover {
    border-color: var(--app-primary-strong);
    color: #fff;
    background: var(--app-primary-strong);
  }
}

.custom-button--add {
  border-color: rgba(16, 163, 148, 0.18);
  color: #087c72;
  background: #eaf8f5;

  &:hover {
    border-color: rgba(16, 163, 148, 0.28);
    color: #06675f;
    background: #dff4f0;
  }
}

.custom-button--delete {
  border-color: rgba(239, 71, 111, 0.16);
  color: #d93560;
  background: #fff0f4;

  &:hover {
    border-color: rgba(239, 71, 111, 0.24);
    color: #bd244c;
    background: #ffe6ed;
  }
}

.custom-button.is-disabled,
.custom-button.is-disabled:hover {
  border-color: #eceef2;
  color: #a8adba;
  background: #f5f6f8;
  box-shadow: none;
  transform: none;
}
</style>
