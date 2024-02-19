// import {
//   AIStreamCallbacksAndOptions,
//   createCallbacksTransformer,
//   createStreamDataTransformer,
//   readableFromAsyncIterable
// } from 'ai'

// const utf8Decoder = new TextDecoder('utf-8')

// interface StreamChunk {
//   text?: string
//   eventType:
//     | 'stream-start'
//     | 'search-queries-generation'
//     | 'search-results'
//     | 'text-generation'
//     | 'citation-generation'
//     | 'stream-end'
// }

// async function processLines(
//   lines: string[],
//   controller: ReadableStreamDefaultController<string>
// ) {
//   for (const line of lines) {
//     console.log('Recdeived from server', line)
//     const { text, is_finished } = JSON.parse(line)

//     // closing the reader is handed in readAndProcessLines
//     if (!is_finished) {
//       controller.enqueue(text)
//     }
//   }
// }

// async function readAndProcessLines(
//   reader: ReadableStreamDefaultReader<Uint8Array>,
//   controller: ReadableStreamDefaultController<string>
// ) {
//   let segment = ''

//   while (true) {
//     const { value: chunk, done } = await reader.read()
//     if (done) {
//       break
//     }

//     segment += utf8Decoder.decode(chunk, { stream: true })

//     const linesArray = segment.split(/\r\n|\n|\r/g)
//     segment = linesArray.pop() || ''

//     await processLines(linesArray, controller)
//   }

//   if (segment) {
//     const linesArray = [segment]
//     await processLines(linesArray, controller)
//   }

//   controller.close()
// }

// function createParser(res: Response) {
//   const reader = res.body?.getReader()

//   return new ReadableStream<string>({
//     async start(controller): Promise<void> {
//       if (!reader) {
//         controller.close()
//         return
//       }

//       await readAndProcessLines(reader, controller)
//     }
//   })
// }

// async function* streamable(reader: ReadableStreamDefaultReader<Uint8Array>) {
//   while (true) {
//     const { value, done } = await reader.read() // Read a chunk from the stream
//     if (done) break // If the stream is finished, exit the loop

//     // Assuming the chunk is a Uint8Array and needs to be parsed as text to get JSON
//     const text = new TextDecoder().decode(value) // Decode Uint8Array to string

//     console.log('text is', text)
//     try {
//       const chunk = JSON.parse(text) // Parse the text as JSON

//       // Now you can check for the properties like 'eventType'
//       if (chunk.eventType === 'text-generation' && chunk.text) {
//         yield chunk.text // Yield the 'text' property if it exists
//       }
//     } catch (error) {
//       console.error('Error parsing chunk as JSON:', error)
//       // Handle parsing error, maybe continue to the next chunk or exit
//     }
//   }
// }

// export function MyStream(
//   response: Response<Uint8Array>,
//   callbacks?: AIStreamCallbacksAndOptions
// ): ReadableStream {
//   return readableFromAsyncIterable(createParser(reader))
//     .pipeThrough(createCallbacksTransformer(callbacks))
//     .pipeThrough(
//       createStreamDataTransformer(callbacks?.experimental_streamData)
//     )
// }
