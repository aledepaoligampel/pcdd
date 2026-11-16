// Cloudflare Pages Function: GET /api/stars
// Reads the repository's star count from GitHub on the server and caches it at the edge,
// so visitors never hit GitHub's unauthenticated rate limit. Always answers 200; when
// GitHub fails the count is null and the page keeps the counter hidden.
// Optional: set a GITHUB_TOKEN secret in Pages to raise the upstream rate limit.
const REPO = 'https://api.github.com/repos/aledepaoligampel/pcdd';
const FRESH = 3600;
const RETRY = 300;

export async function onRequestGet(context) {
  const { request, env } = context;
  const key = new Request(new URL('/api/stars', request.url).toString());
  const cache = typeof caches !== 'undefined' ? caches.default : null;
  const hit = cache && await cache.match(key);
  if (hit) return hit;

  let stars = null;
  try {
    const headers = { 'User-Agent': 'pcdd.dev', Accept: 'application/vnd.github+json' };
    if (env && env.GITHUB_TOKEN) headers.Authorization = 'Bearer ' + env.GITHUB_TOKEN;
    const upstream = await fetch(REPO, { headers });
    if (upstream.ok) {
      const data = await upstream.json();
      if (typeof data.stargazers_count === 'number') stars = data.stargazers_count;
    }
  } catch (e) {
    // Network failure: answer with null below.
  }

  const response = new Response(JSON.stringify({ stars }), {
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'Cache-Control': 'public, max-age=' + (stars === null ? RETRY : FRESH),
      'X-Content-Type-Options': 'nosniff',
    },
  });
  if (cache) context.waitUntil(cache.put(key, response.clone()));
  return response;
}
