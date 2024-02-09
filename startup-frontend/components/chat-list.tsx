import { type Message } from 'ai'

import { Separator } from '@/components/ui/separator'
import { ChatMessage } from '@/components/chat-message'

export interface ChatList {
  messages: Message[]
  data: any
}

export function ChatList({ messages, data }: ChatList) {
  if (!messages.length) {
    return null
  }

  return (
    <div className="relative mx-auto max-w-2xl px-4">
      {data &&
        data.map((item: any, index: number) => <p key={index}>{item.text}</p>)}
      {data &&
        data.map((item: any, index: number) => (
          <p key={index}>{item.sources}</p>
        ))}
      {messages.map((message, index) => (
        <div key={index}>
          <ChatMessage message={message} />
          {index < messages.length - 1 && (
            <Separator className="my-4 md:my-8" />
          )}
        </div>
      ))}
    </div>
  )
}
