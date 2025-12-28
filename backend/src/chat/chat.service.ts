
import { Injectable, Logger, HttpException, HttpStatus } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { ChatRequestDto } from './dto/chat-request.dto';
import { GoogleAuth } from 'google-auth-library';

@Injectable()
export class ChatService {
    private readonly logger = new Logger(ChatService.name);
    private auth: GoogleAuth;
    private project: string;
    private location: string;
    private resourceName: string;
    private apiEndpoint: string;

    constructor(private configService: ConfigService) {
        this.project = this.configService.get<string>('GOOGLE_CLOUD_PROJECT');
        this.location = this.configService.get<string>('GOOGLE_CLOUD_LOCATION');
        this.resourceName = this.configService.get<string>('AGENT_ENGINE_RESOURCE_NAME');
        this.apiEndpoint = `https://${this.location}-aiplatform.googleapis.com/v1/${this.resourceName}`;

        this.auth = new GoogleAuth({
            scopes: ['https://www.googleapis.com/auth/cloud-platform'],
            projectId: this.project,
        });

        this.logger.log(`ChatService initialized (REST) for project: ${this.project}`);
    }

    async chat(chatRequest: ChatRequestDto) {
        const { user_id, message } = chatRequest;
        let { session_id } = chatRequest;
        const client = await this.auth.getClient();
        const token = await client.getAccessToken(); // returns { token, res } or string? depending on version. typically value is token.token

        // Fix token access: recent google-auth-library returns generic object.
        const accessToken = (await this.auth.getAccessToken()) || "";

        if (!session_id) {
            // Create Session via REST
            try {
                const response = await fetch(`${this.apiEndpoint}:query`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${accessToken}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        classMethod: "create_session",
                        input: { user_id: user_id }
                    })
                });

                if (!response.ok) {
                    const errorText = await response.text();
                    this.logger.error(`Create Session Failed: ${response.status} ${errorText}`);
                    throw new Error(`Agent API Error: ${errorText}`);
                }

                const result = await response.json();
                // result matches { output: { id: "..." } } or similar (auto-unwrapped JSON)
                if (result.output && result.output.id) {
                    session_id = result.output.id;
                    this.logger.log(`Created new session: ${session_id}`);
                } else {
                    throw new Error("Invalid session response format");
                }

            } catch (e) {
                this.logger.error("Failed to create session", e);
                throw new HttpException(`Failed to create session: ${e.message}`, HttpStatus.INTERNAL_SERVER_ERROR);
            }
        }

        // Stream Query via REST
        // Note: :streamQuery returns server-sent events or line-delimited JSON? 
        // Vertex AI streamQuery returns a stream of Parseable JSON objects?
        // Let's assume standard JSON response for now to ensure connectivity, or implement stream reading.
        // The python script uses stream_query, which returns a generator.
        // The REST endpoint :streamQuery returns "application/json" but chunked? or "text/event-stream"?
        // Docs say response is a stream of HttpBody.

        // For simplicity validation, let's use NON-Streaming :query first? 
        // BUT the python code calls `stream_query`. If the agent ONLY defines `stream_query` method, we must call match.
        // Agent defines `stream_query`.
        // So we call :streamQuery.

        try {
            const response = await fetch(`${this.apiEndpoint}:streamQuery`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    classMethod: "stream_query",
                    input: {
                        user_id: user_id,
                        session_id: session_id,
                        message: message
                    }
                })
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Agent Stream API Error: ${errorText}`);
            }

            // Reading the stream
            // In Node fetch, response.body is a ReadableStream.
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let fullText = "";
            let responseText = "";

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                const chunk = decoder.decode(value, { stream: true });
                fullText += chunk;

                // Attempt to parse chunks as they might be individual JSON objects
                // This is a naive line-based approach assuming NDJSON or similar structure checking
                // We will accumulate and try to find valid JSONs or just regex extract for robustness
            }

            // Post-processing the full buffer
            // The logs show: {"content": ...}
            // If multiple are sent, they might be concatenated.
            // Let's try to simple regex extract all "text": "..." patterns as a fallback
            // which works well for simple text responses without needing complex stream parsing logic right now.

            // Regex to capture the text content. 
            // Pattern: "text": "..."
            // We need to handle escaped quotes if possible, but basic catch is usually enough for simple flow.
            const textMatches = fullText.matchAll(/"text":\s*"((?:[^"\\]|\\.)*)"/g);
            for (const match of textMatches) {
                // Unescape the JSON string match
                try {
                    responseText += JSON.parse(`"${match[1]}"`);
                } catch (e) {
                    responseText += match[1];
                }
            }

            if (!responseText) {
                // Fallback: if structure is different (e.g. function call), return full debug or empty
                // Check for function calls?
                if (fullText.includes("function_call")) {
                    responseText = "Agent is executing a tool...";
                } else {
                    // Try to see if it's just a raw plain text (unlikely for Vertex)
                    // or simple single JSON
                    try {
                        const json = JSON.parse(fullText);
                        if (json.content && json.content.parts && json.content.parts[0]) {
                            responseText = json.content.parts[0].text || "";
                        }
                    } catch (e) {
                        // ignore
                    }
                }
            }

            if (!responseText && fullText.length > 0) {
                // usage_metadata only? or partial?
                // If we have content but regex failed?
            }

            return {
                session_id: session_id,
                response_text: responseText || "No text response from agent.",
                // raw_debug: fullText.substring(0, 200) + "..."
            };

        } catch (error) {
            this.logger.error("Chat Error", error);
            throw new HttpException(error.message, HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }
}
