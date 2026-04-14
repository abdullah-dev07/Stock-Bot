export async function readStreamResponse(response, messageId, setHistory) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let accumulatedText = '';

  setHistory(prev => [...prev, { role: 'model', text: '', id: messageId }]);

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    accumulatedText += decoder.decode(value, { stream: true });
    setHistory(prev =>
      prev.map(msg =>
        msg.id === messageId ? { ...msg, text: accumulatedText } : msg
      )
    );
  }

  return accumulatedText;
}
