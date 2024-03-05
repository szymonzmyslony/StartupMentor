import {
  TAnyToolDefinitionArray,
  TToolDefinitionMap,
} from "@/lib/utils/tool-definition";
import { CreateMessage, OpenAIStream, ToolCallPayload } from "ai";
import type OpenAI from "openai";
import zodToJsonSchema from "zod-to-json-schema";
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { z } from "zod";
import {
  ChatCompletionMessageParam,
  ChatCompletionTool,
} from "openai/resources/index.mjs";

const consumeStream = async (stream: ReadableStream) => {
  const reader = stream.getReader();
  while (true) {
    const { done } = await reader.read();
    if (done) break;
  }
};

export function runOpenAICompletion<
  T extends Omit<
    Parameters<typeof OpenAI.prototype.chat.completions.create>[0],
    "functions"
  >,
  const TFunctions extends TAnyToolDefinitionArray,
>(
  openai: OpenAI,
  params: T & {
    functions: TFunctions;
  }
) {
  let text = "";
  let hasFunction = false;

  type TToolMap = TToolDefinitionMap<TFunctions>;
  let onTextContent: (text: string, isFinal: boolean) => void = () => {};

  const functionsMap: Record<string, TFunctions[number]> = {};
  for (const fn of params.functions) {
    functionsMap[fn.name] = fn;
  }

  let onFunctionCall = {} as any;

  const { functions, ...rest } = params;
  const toolsMapping: ChatCompletionTool[] = functions.map((fn) => ({
    type: "function",
    function: {
      name: fn.name,
      description: fn.description,
      parameters: zodToJsonSchema(fn.parameters) as Record<string, unknown>,
    },
  }));

  (async () => {
    const response = await openai.chat.completions.create({
      ...rest,
      tool_choice: "auto",
      tools: toolsMapping,
      stream: true,
    });

    let finalMessages: (ChatCompletionMessageParam | CreateMessage)[] = [];

    consumeStream(
      OpenAIStream(response, {
        onToken: (token) => {
          text += token;
          if (text.startsWith("{")) return;

          onTextContent(text, false);
        },
        experimental_onToolCall: async (
          tools: ToolCallPayload,
          appendToolCallMessage
        ) => {
          hasFunction = true;
          const toolCallPayload = tools.tools;
          for (const tool of toolCallPayload) {
            const function_name = tool.func.name;
            // @ts-ignore
            const args = JSON.parse(tool.func.arguments);
            if (!onFunctionCall[function_name]) {
              return;
            }
            onFunctionCall[function_name]?.(args);
          }
        },
        onFinal() {
          console.log("Calling onFinal");
          if (hasFunction) return;
          onTextContent(text, true);
        },
      })
    );
  })();

  return {
    onTextContent: (
      callback: (text: string, isFinal: boolean) => void | Promise<void>
    ) => {
      onTextContent = callback;
    },
    onFunctionCall: <TName extends TFunctions[number]["name"]>(
      name: TName,
      callback: (
        args: z.output<
          TName extends keyof TToolMap
            ? TToolMap[TName] extends infer TToolDef
              ? TToolDef extends TAnyToolDefinitionArray[number]
                ? TToolDef["parameters"]
                : never
              : never
            : never
        >
      ) => void | Promise<void>
    ) => {
      onFunctionCall[name] = callback;
    },
  };
}

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const formatNumber = (value: number) =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(value);

export const runAsyncFnWithoutBlocking = (
  fn: (...args: any) => Promise<any>
) => {
  fn();
};

export const sleep = (ms: number) =>
  new Promise((resolve) => setTimeout(resolve, ms));
