import { AIStreamParser } from 'ai'

function mentorParser(): AIStreamParser {
  return data => {
    console.log('received data', data)
    const json = JSON.parse(data)

    if (json.event === 'text') {
      const text = json.value
      const Parsedtext = JSON.stringify(text)
      const formattedText = `0:${Parsedtext}\n`
      return formattedText
    }
    if (json.event === 'data') {
      const x_data = json.value
      return `2: ${x_data}\n`
    }
  }
}
export default mentorParser
