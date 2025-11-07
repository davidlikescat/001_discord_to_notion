/**
 * Cloudflare Workers - Telegram Bot Webhook Handler
 *
 * 역할:
 * 1. Telegram Bot에서 YouTube URL 수신
 * 2. Supabase에 작업 등록
 * 3. Telegram에 즉시 응답
 *
 * 배포: npx wrangler deploy
 */

export default {
  async fetch(request, env) {
    // CORS 처리
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type'
        }
      });
    }

    // Health check
    if (request.method === 'GET') {
      return new Response('YouTube Summarizer Bot - Running ✅', {
        status: 200,
        headers: { 'Content-Type': 'text/plain' }
      });
    }

    // Telegram Webhook 처리
    if (request.method === 'POST') {
      try {
        const update = await request.json();

        // 메시지 타입 확인
        if (update.message) {
          await handleMessage(update.message, env);
        } else if (update.callback_query) {
          await handleCallbackQuery(update.callback_query, env);
        }

        return new Response('OK', { status: 200 });
      } catch (error) {
        console.error('Error:', error);
        return new Response('Error: ' + error.message, { status: 500 });
      }
    }

    return new Response('Method not allowed', { status: 405 });
  }
};

/**
 * 일반 메시지 처리
 */
async function handleMessage(message, env) {
  const chatId = message.chat.id;
  const text = message.text || '';

  if (!text) return;

  // YouTube URL 추출
  const youtubeUrl = extractYoutubeUrl(text);

  if (!youtubeUrl) {
    await sendTelegramMessage(
      env.TELEGRAM_BOT_TOKEN,
      chatId,
      '❌ YouTube URL을 찾을 수 없습니다.\n\n💡 YouTube 링크를 전송해주세요.'
    );
    return;
  }

  // 채널 선택 버튼 표시
  await sendChannelSelector(env.TELEGRAM_BOT_TOKEN, chatId, youtubeUrl);
}

/**
 * Callback Query 처리 (버튼 클릭)
 */
async function handleCallbackQuery(callbackQuery, env) {
  const chatId = callbackQuery.message.chat.id;
  const data = callbackQuery.data; // 'archive|https://youtube.com/...'
  const userId = callbackQuery.from.id;

  const [channel, youtubeUrl] = data.split('|');

  // Supabase에 작업 등록
  try {
    const response = await fetch(`${env.SUPABASE_URL}/rest/v1/jobs`, {
      method: 'POST',
      headers: {
        'apikey': env.SUPABASE_SERVICE_KEY,
        'Authorization': `Bearer ${env.SUPABASE_SERVICE_KEY}`,
        'Content-Type': 'application/json',
        'Prefer': 'return=representation'
      },
      body: JSON.stringify({
        youtube_url: youtubeUrl,
        telegram_chat_id: chatId,
        telegram_user_id: userId,
        channel: channel,
        status: 'pending',
        created_at: new Date().toISOString()
      })
    });

    if (!response.ok) {
      throw new Error(`Supabase error: ${response.status}`);
    }

    // 작업 등록 성공 메시지
    const channelNames = {
      'archive': '📚 Archive (텍스트 정제)',
      'agent-reference': '🤖 Agent Reference (AI 인사이트)'
    };

    await sendTelegramMessage(
      env.TELEGRAM_BOT_TOKEN,
      chatId,
      `⏳ 요약을 시작합니다!\n\n📺 채널: ${channelNames[channel]}\n🔄 1-2분 내 완료 예상\n\n✅ 완료되면 알림을 보내드릴게요!`
    );

    // Callback Query 응답 (로딩 제거)
    await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/answerCallbackQuery`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        callback_query_id: callbackQuery.id,
        text: '처리 시작!'
      })
    });

  } catch (error) {
    console.error('Supabase error:', error);
    await sendTelegramMessage(
      env.TELEGRAM_BOT_TOKEN,
      chatId,
      `❌ 오류가 발생했습니다: ${error.message}`
    );
  }
}

/**
 * YouTube URL 추출
 */
function extractYoutubeUrl(text) {
  const patterns = [
    /https?:\/\/(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/)[\w-]+(&[\w=%-]*)?/gi,
    /https?:\/\/m\.youtube\.com\/watch\?v=[\w-]+(&[\w=%-]*)?/gi
  ];

  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match) return match[0];
  }

  return null;
}

/**
 * 채널 선택 버튼 전송
 */
async function sendChannelSelector(token, chatId, youtubeUrl) {
  await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      chat_id: chatId,
      text: '📺 어떤 방식으로 요약할까요?',
      reply_markup: {
        inline_keyboard: [
          [
            {
              text: '📚 Archive (텍스트 정제)',
              callback_data: `archive|${youtubeUrl}`
            }
          ],
          [
            {
              text: '🤖 Agent Reference (AI 인사이트)',
              callback_data: `agent-reference|${youtubeUrl}`
            }
          ]
        ]
      }
    })
  });
}

/**
 * Telegram 메시지 전송
 */
async function sendTelegramMessage(token, chatId, text) {
  await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      chat_id: chatId,
      text: text,
      parse_mode: 'HTML'
    })
  });
}
