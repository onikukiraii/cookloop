import sharp from 'sharp'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const publicDir = path.resolve(__dirname, '../public')

// CookLoopのシンボル部分をPWAアイコン用に正方形背景付きで作成
const svgIcon = `
<svg width="512" height="512" viewBox="0 0 512 512" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect width="512" height="512" rx="64" fill="#304D3B"/>
  <g transform="translate(256, 256) scale(4.5) translate(-68, -40)">
    <path d="M45 25V55C45 63.2843 51.7157 70 60 70H70" stroke="#62A176" stroke-width="8" stroke-linecap="round"/>
    <path d="M70 10H80C88.2843 10 95 16.7157 95 25V55C95 63.2843 88.2843 70 80 70" stroke="#C49547" stroke-width="8" stroke-linecap="round"/>
    <path d="M45 25C45 16.7157 51.7157 10 60 10H70" stroke="#62A176" stroke-width="8" stroke-linecap="round"/>
    <circle cx="85" cy="40" r="5" fill="#E14E5F"/>
  </g>
</svg>
`

const sizes = [192, 512]

for (const size of sizes) {
  await sharp(Buffer.from(svgIcon))
    .resize(size, size)
    .png()
    .toFile(path.join(publicDir, `pwa-${size}x${size}.png`))
  console.log(`Generated pwa-${size}x${size}.png`)
}
