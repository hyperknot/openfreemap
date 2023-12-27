# R2 Directory Listing

This is a simple Directory Listing script for [Cloudflare R2](https://developers.cloudflare.com/r2/) and hosted on [Cloudflare Workers](https://workers.cloudflare.com/). It is inspired by the [Directory Listing of Gitea downloads site](https://blog.gitea.com/evolution-of-the-gitea-downloads-site/).

## Usage

Clone this repository, install dependencies and edit the configs:

```bash
git clone https://github.com/cmj2002/r2-dir-list.git
cd r2-dir-list
npm install
mv src/config.ts.example src/config.ts
mv wrangler.toml.example wrangler.toml
```

You should edit:
- `bucketname` in `src/config.ts` and `wrangler.toml` to your bucket name.
- `bucketdomain.example.com` in `src/config.ts` and `wrangler.toml` to your bucket domain. **It must have been set as a [custom domain](https://developers.cloudflare.com/r2/buckets/public-buckets/#custom-domains) of your Cloudflare R2 bucket**.
- `example.com` in `wrangler.toml`'s `zone_name` to yours.
- Other settings like `name`, `desp`, `showPoweredBy` and `legalInfo` in `src/config.ts` to your own.

You may want to search `bucketdomain`, `bucketname` and `example.com` in your code to ensure you have edited all of them.

Then you can run `wrangler deploy` to deploy it to your Cloudflare Workers.

## Demo

https://datasets.caomingjun.com/

This is a production website of mine, which hosts some machine learning datasets used in my papers and codes to share with other reserchers. It is a Cloudflare R2 bucket with this worker in front of it.

## How it works

It will only overwrite the response when all of the following conditions are met:
- Response from R2 has a status of 404
- The requested pathname ends with `/`
- There exist "subdirectories" or "files" under the current "directory" (The quotation marks here are used because directories and files are abstract concepts in object storage)

In such a case, it will generate a HTML page with the list of "subdirectories" and "files" under the current "directory" and return it. Otherwise, it will just return the response from R2. So **putting this worker in front of your R2 bucket will not affect any normal access to your bucket**.
