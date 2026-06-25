# Security Notes

- API Key、SecretId、SecretKey 只能存放在后端 `.env` 或部署平台 Secret 中。
- React 前端、localStorage、报告、PDF、README 和截图不得包含完整密钥。
- `/api/system/provider-status` 只返回配置状态和 masked key 后四位。
- Cached Demo Mode 默认关闭实时 API 消耗，避免公开演示耗尽额度。
- Real Query Mode 需要显式设置 `ENABLE_REAL_QUERY=true` 且后端密钥完整。
- 公开网页线索不等同官方工商、司法或制裁系统核验；报告必须保留人工复核提示。
