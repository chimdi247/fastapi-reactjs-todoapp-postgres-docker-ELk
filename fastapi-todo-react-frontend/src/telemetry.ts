/**
 * Browser OpenTelemetry (traces).
 *
 *  - Auto-instrumentation: document load/navigation timings and every fetch().
 *  - W3C `traceparent` is injected on same-origin API calls, so a click in the
 *    browser, the nginx hop, the FastAPI request and the SQL queries all share
 *    one trace id (visible in Kibana, and in backend log lines as `trace_id`).
 *  - Manual instrumentation: see `ui.login` span in pages/Login.tsx and the
 *    global error handlers below.
 *
 * Spans are POSTed to /otlp/v1/traces (same origin, so no CORS), which nginx
 * proxies to the OpenTelemetry Collector.
 * Disable with VITE_OTEL_ENABLED=false at build time.
 */
import { trace, SpanStatusCode } from '@opentelemetry/api';
import { ZoneContextManager } from '@opentelemetry/context-zone';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { registerInstrumentations } from '@opentelemetry/instrumentation';
import { DocumentLoadInstrumentation } from '@opentelemetry/instrumentation-document-load';
import { FetchInstrumentation } from '@opentelemetry/instrumentation-fetch';
import { resourceFromAttributes } from '@opentelemetry/resources';
import { BatchSpanProcessor } from '@opentelemetry/sdk-trace-base';
import { WebTracerProvider } from '@opentelemetry/sdk-trace-web';
import { ATTR_SERVICE_NAME, ATTR_SERVICE_VERSION } from '@opentelemetry/semantic-conventions';

const enabled = import.meta.env.VITE_OTEL_ENABLED !== 'false';
const endpoint: string = import.meta.env.VITE_OTEL_TRACES_URL ?? '/otlp/v1/traces';

if (enabled) {
    const provider = new WebTracerProvider({
        resource: resourceFromAttributes({
            [ATTR_SERVICE_NAME]: 'todo-frontend',
            [ATTR_SERVICE_VERSION]: import.meta.env.VITE_APP_VERSION ?? '0.1.0',
            'deployment.environment': import.meta.env.VITE_ENVIRONMENT ?? 'local',
        }),
        spanProcessors: [
            new BatchSpanProcessor(new OTLPTraceExporter({ url: endpoint }), {
                scheduledDelayMillis: 3000,
                maxExportBatchSize: 50,
            }),
        ],
    });

    // ZoneContextManager keeps the active span across await/async boundaries.
    provider.register({ contextManager: new ZoneContextManager() });

    registerInstrumentations({
        instrumentations: [
            new DocumentLoadInstrumentation(),
            new FetchInstrumentation({
                // Never trace the exporter's own traffic.
                ignoreUrls: [/\/otlp\//],
                // Same-origin requests get traceparent by default; list any extra
                // cross-origin API hosts here if you ever call one directly.
                propagateTraceHeaderCorsUrls: [],
            }),
        ],
    });

    const tracer = trace.getTracer('todo-frontend.errors');
    const recordError = (name: string, error: unknown) => {
        const span = tracer.startSpan(name);
        span.recordException(error instanceof Error ? error : new Error(String(error)));
        span.setStatus({ code: SpanStatusCode.ERROR });
        span.end();
    };
    window.addEventListener('error', (e) => recordError('ui.unhandled_error', e.error ?? e.message));
    window.addEventListener('unhandledrejection', (e) => recordError('ui.unhandled_rejection', e.reason));
}
