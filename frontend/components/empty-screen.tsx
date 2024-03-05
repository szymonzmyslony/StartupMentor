import { Button } from "@/components/ui/button";
import { ExternalLink } from "@/components/external-link";
import { IconArrowRight } from "@/components/ui/icons";

const exampleMessages = [
  {
    heading: "How to come up with a startup idea?",
    message: "How to come up with a startup idea?",
  },
  {
    heading: "Go to market for seria A B2B startup",
    message: "Go to market for seria A B2B startup",
  },
  {
    heading: "Help me with my pitch-deck",
    message: "Help me with my pitch-deck",
  },
];

export function EmptyScreen({
  submitMessage,
}: {
  submitMessage: (message: string) => void;
}) {
  return (
    <div className="mx-auto max-w-2xl px-4">
      <div className="rounded-lg border bg-background p-8 mb-4">
        <h1 className="mb-2 text-lg font-semibold">
          Welcome to AI StartUp Mentor
        </h1>
        <p className="mb-2 leading-normal text-muted-foreground">
          This is a demo of an interactive startup mentor based on the YC
          library.
        </p>

        <p className="leading-normal text-muted-foreground">Try an example:</p>
        <div className="mt-4 flex flex-col items-start space-y-2 mb-4">
          {exampleMessages.map((message, index) => (
            <Button
              key={index}
              variant="link"
              className="h-auto p-0 text-base"
              onClick={async () => {
                submitMessage(message.message);
              }}
            >
              <IconArrowRight className="mr-2 text-muted-foreground" />
              {message.heading}
            </Button>
          ))}
        </div>
      </div>
      <p className="leading-normal text-muted-foreground text-[0.8rem] text-center">
        Note: This is not real financial advice.
      </p>
    </div>
  );
}
