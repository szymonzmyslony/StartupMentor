export const StatusMessage = ({ text }: { text: string }) => (
  <div className="flex items-center justify-between px-4 py-2 my-2 text-sm font-medium text-info bg-info-background rounded-md">
    <span>{text}</span>
  </div>
)
