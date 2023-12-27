import { Env } from './types';
import { renderTemplFull } from './render';
import { getSiteConfig } from './config';

export default {
    async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
        const originResponse = await fetch(request);
        // if status is not 404 or request path not end with '/', return origin response
        if ((originResponse.status !== 404) || (originResponse.url.slice(-1) !== '/')) {
            return originResponse;
        }
        const url = new URL(request.url);
        const domain = url.hostname;
        const path = url.pathname;
        // remove the leading '/'
        const objectKey = path.slice(1);
        const siteConfig = getSiteConfig(env, domain);
        if (!siteConfig) {
            // TODO: Should send a email to notify the admin
            return originResponse;
        }
        const bucket = siteConfig.bucket;
        const index = await bucket.list({
            // TODO: Should manage limit here, but since I won't have more than 1000 files in a single folder, I just ignore it
            prefix: objectKey,
            delimiter: '/',
            include: ['httpMetadata', 'customMetadata']
        });
        // if no object found, return origin response
        if (index.objects.length === 0 && index.delimitedPrefixes.length === 0) {
            return originResponse;
        }
        return new Response(
            renderTemplFull(index.objects, index.delimitedPrefixes, path, siteConfig),
            {
                headers: {
                    'Content-Type': 'text/html; charset=utf-8',
                },
                status: 200,
            },
        );
    },
};
