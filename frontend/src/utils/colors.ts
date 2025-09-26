const keywordColorMap: Record<string, string> = {
  운동: 'bg-positive',
  스터디: 'bg-positive',
  학습: 'bg-positive',
  회의: 'bg-neutral',
  마감: 'bg-warning',
  경고: 'bg-warning',
  중요: 'bg-warning',
};

export const getEventColorClass = (summary: string) => {
  const matched = Object.entries(keywordColorMap).find(([keyword]) => summary.includes(keyword));
  if (matched) {
    return matched[1];
  }
  return 'bg-neutral';
};
