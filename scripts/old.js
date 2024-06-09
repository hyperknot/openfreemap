/**
 * Welcome to Cloudflare Workers!
 *
 * This is a template for a Scheduled Worker: a Worker that can run on a
 * configurable interval:
 * https://developers.cloudflare.com/workers/platform/triggers/cron-triggers/
 *
 * - Run `npm run dev` in your terminal to start a development server
 * - Run `curl "http://localhost:8787/__scheduled?cron=*+*+*+*+*"` to see your worker in action
 * - Run `npm run deploy` to publish your worker
 *
 * Learn more at https://developers.cloudflare.com/workers/
 */

const AREAS = ['planet', 'monaco']

async function handleArea(area, env) {
  const deployedVersion = await getDeployedVersion(area)

  const http_hosts = env.HTTP_HOST_LIST.split(',')
    .map(s => s.trim())
    .filter(Boolean)

  for (const host of http_hosts) {
    await checkHost(host, area, deployedVersion)
  }
}

async function getDeployedVersion(area) {
  const response = await fetch(`https://assets.openfreemap.com/versions/deployed_${area}.txt`)

  if (!response.ok) {
    throw new Error(`HTTP error! Status: ${response.status}`)
  }

  const content = await response.text()
  return content.trim()
}

async function checkHost(host, area, version) {
  // using HTTP as the HTTPS needs custom resolvers
  // discussion links:
  // https://community.letsencrypt.org/t/understanding-server-name-resolving-vs-host-headers-in-https/219784
  // https://community.cloudflare.com/t/how-to-resolve-https-in-a-js-worker/669506

  const url = `http://${host}/${area}/${version}/14/8529/5975.pbf`
  console.log(url)
  const response = await fetch(url, {
    method: 'HEAD',
    headers: {
      Host: 'direct.openfreemap.org',
    },
  })

  console.log(response)
}

export default {
  async fetch(req) {
    const url = new URL(req.url)
    url.pathname = '/__scheduled'
    url.searchParams.append('cron', '* * * * *')
    return new Response(
      `To test the scheduled handler, ensure you have used the "--test-scheduled" then try running "curl ${url.href}".`,
    )
  },

  // The scheduled handler is invoked at the interval set in our wrangler.toml's
  // [[triggers]] configuration.
  async scheduled(event, env, ctx) {
    const url = 'http://direct.openfreemap.org/styles/liberty'

    const response = await fetch(url, { cf: { resolveOverride: '1.1.1.1' } })

    console.log(response, response.ok)

    // return
    //
    // for (const area of AREAS) {
    //   await handleArea(area, env)
    // }
    //
    // // We'll keep it simple and make an API call to a Cloudflare API:
    // let resp = await fetch('https://api.cloudflare.com/client/v4/ips')
    // let wasSuccessful = resp.ok ? 'success' : 'fail'
    //
    // // You could store this result in KV, write to a D1 Database, or publish to a Queue.
    // // In this template, we'll just log the result:
    // console.log(`trigger fired at ${event.cron}: ${wasSuccessful}`)
  },
}
