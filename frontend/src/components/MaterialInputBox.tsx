const MAX_LENGTH = 20000;

export function MaterialInputBox({ value, onChange }: { value: string; onChange: (value: string) => void }) {
  return (
    <section className="material-input">
      <label>
        <span>可选：供应商补充材料</span>
        <p className="field-hint">这段材料会随你下方选择的供应商一起提交，系统会从中抽取风险证据并参与评分。</p>
        <textarea
          value={value}
          maxLength={MAX_LENGTH}
          onChange={(event) => onChange(event.target.value)}
          placeholder="可粘贴供应商官网介绍、工商信息摘要、新闻报道、交付延期说明、合同争议描述等。"
        />
      </label>
      <small>{value.length} / {MAX_LENGTH}</small>
    </section>
  );
}
