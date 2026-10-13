<template>
  <div class="pagination-wrapper">
    <el-pagination
      :current-page="currentPage"
      :page-size="pageSize"
      :page-sizes="pageSizeOptions"
      :total="total"
      layout="sizes, prev, pager, next, total"
      background
      @size-change="handleSizeChange"
      @current-change="handlePageChange"
    />
  </div>
</template>

<script>
export default {
  name: 'Pagination',
  props: {
    total: {
      type: Number,
      default: 0
    },
    currentPage: {
      type: Number,
      default: 1
    },
    pageSize: {
      type: Number,
      default: 10
    },
    pageSizeOptions: {
      type: Array,
      default: () => [10, 20, 50, 100]
    }
  },
  methods: {
    handleSizeChange(val) {
      this.$emit('size-change', val);
    },
    handlePageChange(page) {
      this.$emit('page-change', page);
    }
  }
};
</script>

<style lang="scss" scoped>
::v-deep .el-pagination {
  .btn-next,
  .btn-prev,
  .el-pager li {
    background: transparent !important;
    min-width: 32px !important;
    border-radius: 8px;
  }
  .el-pager li:not(.disabled).active {
    background: var(--app-primary) !important;
    border-radius: 8px;
    box-shadow: 0 3px 8px rgba(70, 87, 232, 0.20);
    color: #fff;
    font-weight: 600;
  }
}
</style>
