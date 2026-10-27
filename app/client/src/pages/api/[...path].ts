import type { APIRoute } from "astro";

export const prerender = false;

const API_SERVER_URL = process.env.API_SERVER_URL || "http://127.0.0.1:5100";

async function forward({ request, params }: Parameters<APIRoute>[0]) {
  const apiPath = (params.path || "")
    .split("/")
    .filter(Boolean)
    .map(encodeURIComponent)
    .join("/");
  const upstreamUrl = new URL(`/api/${apiPath}`, API_SERVER_URL);
  upstreamUrl.search = new URL(request.url).search;

  const headers = new Headers();
  for (const name of ["content-type", "cookie", "x-csrf-token"]) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }

  const hasBody = request.method !== "GET" && request.method !== "HEAD";
  try {
    const upstream = await fetch(upstreamUrl, {
      method: request.method,
      headers,
      body: hasBody ? await request.arrayBuffer() : undefined,
    });
    const responseHeaders = new Headers();
    for (const name of [
      "content-type",
      "content-disposition",
      "cache-control",
      "set-cookie",
      "retry-after",
      "x-content-type-options",
      "referrer-policy",
    ]) {
      const value = upstream.headers.get(name);
      if (value) responseHeaders.set(name, value);
    }
    return new Response(await upstream.arrayBuffer(), {
      status: upstream.status,
      headers: responseHeaders,
    });
  } catch {
    return Response.json(
      { error: "تعذّر الاتصال بخدمة دفتر الذكريات." },
      { status: 502, headers: { "Cache-Control": "no-store" } },
    );
  }
}

export const GET: APIRoute = forward;
export const POST: APIRoute = forward;
export const DELETE: APIRoute = forward;
