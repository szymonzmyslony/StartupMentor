import { UseChatHelpers } from 'ai/react'

import { Button } from '@/components/ui/button'
import { ExternalLink } from '@/components/external-link'
import { IconArrowRight } from '@/components/ui/icons'

interface EmptyScreenProps extends Pick<UseChatHelpers, 'append' | 'setInput'> {
  id?: string
}

const exampleMessages = [
  {
    heading: 'How do I come up with an idea?',
    message: `How do I come up with an idea?`
  },
  {
    heading: 'How do I validate a start-up idea?',
    message: 'How do I validate a start-up idea?'
  },
  {
    heading: 'I need help with my pitch deck',
    message: `I need help with my pitch deck`
  }
]

export function EmptyScreen({ setInput, append, id }: EmptyScreenProps) {
  return (
    <div className="mx-auto max-w-2xl px-4">
      <div className="rounded-lg border bg-background p-8">
        <h1 className="mb-2 text-lg font-semibold">
          Welcome to Startup Mentor
        </h1>
        <p className="mb-2 leading-normal text-muted-foreground">
          We help you build the company of you dreams
        </p>
        <p className="leading-normal text-muted-foreground">
          Some of the things we can help you with:
        </p>

        <div className="mt-4 flex flex-col items-start space-y-2">
          {exampleMessages.map((message, index) => (
            <Button
              key={index}
              variant="link"
              className="h-auto p-0 text-base"
              onClick={async () => {
                setInput(message.message)
                await append({
                  id,
                  content: message.message,
                  role: 'user'
                })
                setInput('')
              }}
            >
              <IconArrowRight className="mr-2 text-muted-foreground" />
              {message.heading}
            </Button>
          ))}
        </div>
      </div>
    </div>
  )
}
