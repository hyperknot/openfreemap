export type Env = {
    [K in `BUCKET_${string}`]: R2Bucket;
};

export interface SiteConfig {
    name: string;
    bucket: R2Bucket;
    desp: {
        [path: string]: string;
    };
    legalInfo?: string;
    showPoweredBy?: boolean;
    favicon?: string;
}