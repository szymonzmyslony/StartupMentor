import "server-only";

import {
  createAI,
  createStreamableUI,
  getAIState,
  getMutableAIState,
} from "ai/rsc";
import OpenAI from "openai";

import {
  spinner,
  BotCard,
  BotMessage,
  SystemMessage,
  Stock,
} from "@/components/llm-stocks";

import {
  runAsyncFnWithoutBlocking,
  sleep,
  formatNumber,
  runOpenAICompletion,
} from "@/lib/utils";
import { z } from "zod";
import { StockSkeleton } from "@/components/llm-stocks/stock-skeleton";
import getSupabase from "@/lib/supabase";
import { runOpenAiTextCompletion } from "@/lib/utils/textCall";

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY || "",
});

async function confirmPurchase(symbol: string, price: number, amount: number) {
  "use server";

  const aiState = getMutableAIState<typeof AI>();

  const purchasing = createStreamableUI(
    <div className="inline-flex items-start gap-1 md:items-center">
      {spinner}
      <p className="mb-2">
        Purchasing {amount} ${symbol}...
      </p>
    </div>
  );

  const systemMessage = createStreamableUI(null);

  runAsyncFnWithoutBlocking(async () => {
    // You can update the UI at any point.
    await sleep(1000);

    purchasing.update(
      <div className="inline-flex items-start gap-1 md:items-center">
        {spinner}
        <p className="mb-2">
          Purchasing {amount} ${symbol}... working on it...
        </p>
      </div>
    );

    await sleep(1000);

    purchasing.done(
      <div>
        <p className="mb-2">
          You have successfully purchased {amount} ${symbol}. Total cost:{" "}
          {formatNumber(amount * price)}
        </p>
      </div>
    );

    systemMessage.done(
      <SystemMessage>
        You have purchased {amount} shares of {symbol} at ${price}. Total cost ={" "}
        {formatNumber(amount * price)}.
      </SystemMessage>
    );

    aiState.done([
      ...aiState.get(),
      {
        role: "system",
        content: `[User has purchased ${amount} shares of ${symbol} at ${price}. Total cost = ${
          amount * price
        }]`,
      },
    ]);
  });

  return {
    purchasingUI: purchasing.value,
    newMessage: {
      id: Date.now(),
      display: systemMessage.value,
    },
  };
}

async function submitUserMessage(content: string) {
  "use server";

  const aiState = getMutableAIState<typeof AI>();
  aiState.update([
    ...aiState.get(),
    {
      role: "user",
      content,
    },
  ]);

  const reply = createStreamableUI(
    <BotMessage className="items-center">{spinner}</BotMessage>
  );

  const currentMessages = aiState.get().map((info: any) => ({
    role: info.role,
    content: info.content,
    name: info.name,
  }));

  const completion = runOpenAICompletion(openai, {
    model: "gpt-3.5-turbo",
    stream: true,
    messages: [
      {
        role: "system",
        content: `\
You are a startup mentor help users come up with their potential solutions to their problem.
If it is not startup related question, do not answer and guide the user to startups. 
Generate a set of diverse quries and call  \`match_chunks\` to fetch from the startup mentors database.
Always call match_chunks unless you are probing for more context.
`,
      },
      ...currentMessages,
    ],
    functions: [
      {
        name: "match_chunks",
        description:
          "Fetches relevant startup advice based on the list of quries",
        parameters: z.object({
          queries: z
            .array(z.string())
            .describe(
              "List of queries. Should range from general to specific. At least 3."
            ),
        }),
      },
    ],
    temperature: 0,
  });

  completion.onTextContent((content: string, isFinal: boolean) => {
    reply.update(<BotMessage>{content}</BotMessage>);
    if (isFinal) {
      reply.done();
      aiState.done([...aiState.get(), { role: "assistant", content }]);
    }
  });

  completion.onFunctionCall("match_chunks", async ({ queries }) => {
    const content = await getSupabase().matchChunks(queries);

    // get all but last messages
    const previousMessages = currentMessages.slice(0, -1);
    const lastMessage = currentMessages[currentMessages.length - 1];
    const finalMessage = {
      ...lastMessage,
      content: `Answer the following question using only the context provided. Question: ${lastMessage.content}. Context: ${content}`,
    };

    const final_messages = [...previousMessages, finalMessage];
    console.log("final_messages", final_messages);

    const second_completion = runOpenAiTextCompletion(openai, {
      model: "gpt-3.5-turbo",
      stream: true,
      messages: final_messages,
      temperature: 0,
    });

    second_completion.onTextContent((content: string, isFinal: boolean) => {
      reply.update(<BotMessage>{content}</BotMessage>);
      if (isFinal) {
        reply.done();
        aiState.done([...aiState.get(), { role: "assistant", content }]);
      }
    });

    reply.update(<BotMessage>Fetching {queries}</BotMessage>);
  });

  return {
    id: Date.now(),
    display: reply.value,
  };
}

// Define necessary types and create the AI.

const initialAIState: {
  role: "user" | "assistant" | "system" | "function";
  content: string;
  id?: string;
  name?: string;
}[] = [];

const initialUIState: {
  id: number;
  display: React.ReactNode;
}[] = [];

export const AI = createAI({
  actions: {
    submitUserMessage,
    confirmPurchase,
  },
  initialUIState,
  initialAIState,
});
