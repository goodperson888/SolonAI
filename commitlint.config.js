module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    // type 类型定义
    'type-enum': [
      2,
      'always',
      [
        'feat',     // 新功能
        'fix',      // 修复bug
        'docs',     // 文档更新
        'style',    // 代码格式（不影响功能）
        'refactor', // 重构
        'perf',     // 性能优化
        'test',     // 测试
        'chore',    // 构建/工具/依赖
        'revert',   // 回退
        'ci',       // CI/CD
      ],
    ],
    // type 必须小写
    'type-case': [2, 'always', 'lower-case'],
    // type 不能为空
    'type-empty': [2, 'never'],
    // subject 不能为空
    'subject-empty': [2, 'never'],
    // subject 不超过 72 个字符
    'subject-max-length': [2, 'always', 72],
    // body 每行不超过 100 个字符
    'body-max-line-length': [2, 'always', 100],
  },
}
