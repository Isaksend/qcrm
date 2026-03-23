import type { AIInsight } from '../types'
import { mockAIResponses } from '../data/mock'

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export async function getDemoInsight(
  entityType: string,
  entityId: string
): Promise<AIInsight> {
  await delay(1000 + Math.random() * 1000)
  const key = entityId
  const insight = mockAIResponses[key]
  if (insight) return insight
  return {
    id: `ai-${entityType}-${entityId}`,
    entityType: entityType as AIInsight['entityType'],
    entityId,
    category: 'analysis',
    title: `Analysis for ${entityType} ${entityId}`,
    content:
      'No specific analysis available for this entity yet. Continue tracking engagement metrics and activity patterns to generate actionable insights.',
    confidence: 50,
    suggestions: [
      'Increase engagement touchpoints',
      'Gather more data for accurate analysis',
      'Check back after more interactions',
    ],
  }
}

export async function getLiveInsight(
  entityType: string,
  entityData: Record<string, unknown>,
  apiKey: string
): Promise<AIInsight> {
  const prompt = buildPrompt(entityType, entityData)

  const response = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=${apiKey}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contents: [{ parts: [{ text: prompt }] }],
      }),
    }
  )

  if (!response.ok) {
    throw new Error(`Gemini API error: ${response.status}`)
  }

  const data = await response.json()
  const text =
    data.candidates?.[0]?.content?.parts?.[0]?.text ?? 'No response generated.'

  return parseAIResponse(entityType, entityData, text)
}

function buildPrompt(
  entityType: string,
  entityData: Record<string, unknown>
): string {
  const dataStr = JSON.stringify(entityData, null, 2)
  return `You are a CRM AI assistant. Analyze this ${entityType} data and provide actionable sales insights.

Data:
${dataStr}

Respond in this exact JSON format:
{
  "title": "Brief insight title",
  "category": "risk|opportunity|coaching|prediction|analysis",
  "content": "2-3 sentence analysis with specific, actionable insights",
  "confidence": 75,
  "suggestions": ["Action item 1", "Action item 2", "Action item 3"]
}`
}

function parseAIResponse(
  entityType: string,
  entityData: Record<string, unknown>,
  text: string
): AIInsight {
  try {
    const jsonMatch = text.match(/\{[\s\S]*\}/)
    if (jsonMatch) {
      const parsed = JSON.parse(jsonMatch[0])
      return {
        id: `ai-live-${Date.now()}`,
        entityType: entityType as AIInsight['entityType'],
        entityId: (entityData.id as string) ?? null,
        category: parsed.category ?? 'analysis',
        title: parsed.title ?? 'AI Analysis',
        content: parsed.content ?? text,
        confidence: parsed.confidence ?? 70,
        suggestions: parsed.suggestions ?? [],
      }
    }
  } catch {
    // fallback below
  }

  return {
    id: `ai-live-${Date.now()}`,
    entityType: entityType as AIInsight['entityType'],
    entityId: (entityData.id as string) ?? null,
    category: 'analysis',
    title: 'AI Analysis',
    content: text,
    confidence: 70,
    suggestions: [],
  }
}
