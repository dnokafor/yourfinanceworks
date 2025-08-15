import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

interface TemplateSelectorProps {
  value: string;
  onChange: (value: string) => void;
}

const templates = [
  { id: 'modern', name: 'Modern (Blue)' },
  { id: 'classic', name: 'Classic (Black)' },
];

export const TemplateSelector = ({ value, onChange }: TemplateSelectorProps) => {
  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger className="w-48">
        <SelectValue placeholder="Select template" />
      </SelectTrigger>
      <SelectContent>
        {templates.map((template) => (
          <SelectItem key={template.id} value={template.id}>
            {template.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
};