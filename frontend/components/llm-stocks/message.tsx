"use client";

import { AI } from "@/app/action";
import { IconAI, IconUser } from "@/components/ui/icons";
import { cn } from "@/lib/utils";
import { useActions, useUIState } from "ai/rsc";
import { useState } from "react";

// Different types of message bubbles.

export function UserMessage({ children }: { children: React.ReactNode }) {
  return (
    <div className="group relative flex items-start md:-ml-12">
      <div className="flex h-8 w-8 shrink-0 select-none items-center justify-center rounded-md border shadow-sm bg-background">
        <IconUser />
      </div>
      <div className="ml-4 flex-1 space-y-2 overflow-hidden px-1">
        {children}
      </div>
    </div>
  );
}

export function BotMessage({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("group relative flex items-start md:-ml-12", className)}>
      <div className="flex h-8 w-8 shrink-0 select-none items-center justify-center rounded-md border shadow-sm bg-primary text-primary-foreground">
        <IconAI />
      </div>
      <div className="ml-4 flex-1 space-y-2 overflow-hidden px-1">
        {children}
      </div>
    </div>
  );
}

export function BotCard({
  children,
  showAvatar = true,
}: {
  children: React.ReactNode;
  showAvatar?: boolean;
}) {
  return (
    <div className="group relative flex items-start md:-ml-12">
      <div
        className={cn(
          "flex h-8 w-8 shrink-0 select-none items-center justify-center rounded-md border shadow-sm bg-primary text-primary-foreground",
          !showAvatar && "invisible"
        )}
      >
        <IconAI />
      </div>
      <div className="ml-4 flex-1 px-1">{children}</div>
    </div>
  );
}

export function SystemMessage({ children }: { children: React.ReactNode }) {
  return (
    <div
      className={
        "mt-2 flex items-center justify-center gap-2 text-xs text-gray-500"
      }
    >
      <div className={"max-w-[600px] flex-initial px-2 py-2"}>{children}</div>
    </div>
  );
}

function Answer({
  answer,
  onClick,
  isSelected,
}: {
  answer: string;
  onClick: () => void;
  isSelected: boolean;
}) {
  return (
    <div
      className={`cursor-pointer rounded-md border shadow-sm px-4 py-2 ${
        isSelected ? "bg-blue-100 border-blue-500" : "hover:bg-gray-100"
      }`}
      onClick={onClick}
    >
      {answer}
    </div>
  );
}

function CustomAnswer({
  onSubmit,
}: {
  onSubmit: (customAnswer: string) => void;
}) {
  const [inputValue, setInputValue] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault(); // Prevent form from refreshing the page on submit
    if (inputValue.trim()) {
      onSubmit(inputValue.trim());
    }
  };

  return (
    <form className="flex items-center space-x-2" onSubmit={handleSubmit}>
      <input
        type="text"
        placeholder="Your answer..."
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        className="flex-1 rounded-md border px-4 py-2"
      />
      <button
        type="submit"
        className="rounded-md bg-primary text-white px-4 py-2 hover:bg-primary-dark"
      >
        Submit
      </button>
    </form>
  );
}

function Question({ question }: { question: string }) {
  return <div className="mb-4 text-lg font-semibold">{question}</div>;
}

export function QuestionWithAnswer({
  question,
  answers,
  allowCustomAnswer = true, // Optional prop to enable/disable custom answers
}: {
  question: string;
  answers: string[];
  allowCustomAnswer?: boolean;
}) {
  const [messages, setMessages] = useUIState<typeof AI>();
  const { submitUserMessage } = useActions<typeof AI>();
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
  const onAnswerSelect = async (answer: string) => {
    const responseMessage = await submitUserMessage(answer);
    setMessages((currentMessages) => [...currentMessages, responseMessage]);
  };

  const handleAnswerSelect = async (answer: string) => {
    if (!selectedAnswer) {
      // Only allow selection if no answer has been selected yet
      setSelectedAnswer(answer);
      await onAnswerSelect(answer);
    }
  };

  const handleCustomAnswerSubmit = async (customAnswer: string) => {
    if (!selectedAnswer) {
      // Only allow submission if no answer has been selected yet
      setSelectedAnswer(customAnswer);
      await onAnswerSelect(customAnswer);
    }
  };

  return (
    <div>
      <Question question={question} />
      <div className="space-y-2">
        {answers.map((answer, index) => (
          <Answer
            key={index}
            answer={answer}
            onClick={() => handleAnswerSelect(answer)}
            isSelected={answer === selectedAnswer}
          />
        ))}
        {allowCustomAnswer && (
          <CustomAnswer onSubmit={handleCustomAnswerSubmit} />
        )}
      </div>
    </div>
  );
}
