import { CreateMessage, OpenAIStream, ToolCallPayload } from "ai";
import type OpenAI from "openai";

const consumeStream = async (stream: ReadableStream) => {
  const reader = stream.getReader();
  while (true) {
    const { done } = await reader.read();
    if (done) break;
  }
};
export function runOpenAiTextCompletion<
  T extends Parameters<typeof OpenAI.prototype.chat.completions.create>[0],
>(openai: OpenAI, params: T) {
  let text = "";

  let onTextContent: (text: string, isFinal: boolean) => void = () => {};

  // Since 'functions' is no longer part of params, we can directly use 'params'
  (async () => {
    const response = await openai.chat.completions.create({
      ...params, // Directly spread 'params' without omitting 'functions'
      stream: true,
    });

    consumeStream(
      OpenAIStream(response, {
        onToken: (token) => {
          text += token;
          if (text.startsWith("{")) return;

          onTextContent(text, false);
        },

        onFinal() {
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
  };
}
