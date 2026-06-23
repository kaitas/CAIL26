#!/usr/bin/env node
/**
 * NobelEngine CI バリデータ（依存ゼロ / Node ESM）
 *
 * AGENTS.md のガードレールを機械的に検査する。CI でも `npm run validate`
 * 相当としてローカルでも実行可能。1つでも失敗すれば exit code 1 を返す。
 *
 *  1. 必須ファイルの存在
 *  2. 単一ファイル原則（ローカル相対 src/href を持つ <script>/<link> を禁止。CDN https のみ許可）
 *  3. 主要関数の存在（applyCustomThemeColor 等のガードレール対象を含む）
 *  4. 多言語（ja/zh）整合（details ⇔ detailsZh、panic ⇔ pressure の件数一致）
 *  5. HTML 基本健全性（<html>/<body> の対応、非空）
 *
 * 使い方: node scripts/validate.mjs
 */
import { readFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const read = (p) => readFileSync(join(ROOT, p), 'utf8');

let failures = 0;
const ok = (msg) => console.log(`  ✅ ${msg}`);
const ng = (msg) => { console.log(`  ❌ ${msg}`); failures++; };
const section = (t) => console.log(`\n▶ ${t}`);
const count = (s, sub) => s.split(sub).length - 1;

// ---------------------------------------------------------------------------
// 1. 必須ファイルの存在
// ---------------------------------------------------------------------------
section('必須ファイルの存在');
const REQUIRED_FILES = [
  'index.html',
  'nobelengine_agents_portal.html',
  'AGENTS.md',
  'README.md',
  '.nojekyll',
];
for (const f of REQUIRED_FILES) {
  existsSync(join(ROOT, f)) ? ok(`${f} が存在`) : ng(`${f} が見つかりません`);
}

// 以降の検査は index.html 前提
if (!existsSync(join(ROOT, 'index.html'))) {
  console.log('\nindex.html が無いため以降の検査を中止します。');
  process.exit(1);
}
const html = read('index.html');

// ---------------------------------------------------------------------------
// 2. 単一ファイル原則（ローカル相対アセット参照を禁止）
// ---------------------------------------------------------------------------
section('単一ファイル原則（ローカル相対アセット参照の禁止）');
// <script src="..."> / <link href="..."> のうち http(s):// でも data: でもないものを違反とみなす
const assetRefs = [...html.matchAll(/<(?:script|link)\b[^>]*\b(?:src|href)\s*=\s*"([^"]*)"/gi)]
  .map((m) => m[1]);
const localRefs = assetRefs.filter((u) => !/^(https?:|data:|#)/i.test(u));
if (localRefs.length === 0) {
  ok(`外部CDN(https)のみを参照（ローカルアセット参照なし / 検出 ${assetRefs.length} 件すべて許可）`);
} else {
  ng(`ローカル相対アセット参照が ${localRefs.length} 件あります: ${localRefs.join(', ')}`);
}

// ---------------------------------------------------------------------------
// 3. 主要関数の存在（ガードレール対象を含む）
// ---------------------------------------------------------------------------
section('主要関数・ガードレールの存在');
const REQUIRED_FNS = [
  'applyCustomThemeColor', // テーマ動的反映（破壊禁止）
  'initNarrativeTrackerUI',
  'initMagicTodoUI',
  'initGlossaryDictionaryUI',
  'loadProject',
  'writeLog',
];
for (const fn of REQUIRED_FNS) {
  const re = new RegExp(`function\\s+${fn}\\s*\\(`);
  re.test(html) ? ok(`${fn}() を定義`) : ng(`${fn}() の定義が見つかりません`);
}
// データベースの存在
/\bgameDatabase\b/.test(html) ? ok('gameDatabase が存在') : ng('gameDatabase が見つかりません');
/\bmagicTodoDatabase\b/.test(html) ? ok('magicTodoDatabase が存在') : ng('magicTodoDatabase が見つかりません');

// ---------------------------------------------------------------------------
// 4. 多言語（ja/zh）整合
// ---------------------------------------------------------------------------
section('多言語（ja / zh）整合');
const pairs = [
  ['details:', 'detailsZh:'], // ナラティブ証拠テキスト
  ['panic:', 'pressure:'],    // Magic ToDo 構造（各レベルに両方必須）
];
for (const [a, b] of pairs) {
  const ca = count(html, a);
  const cb = count(html, b);
  ca === cb && ca > 0
    ? ok(`${a} (${ca}) ⇔ ${b} (${cb}) 件数一致`)
    : ng(`${a} (${ca}) と ${b} (${cb}) の件数が不一致`);
}

// ---------------------------------------------------------------------------
// 4.5 参照アセット（画像）の実在チェック
//     index.html が src/href で参照する assets/ のローカル画像が実在するか
// ---------------------------------------------------------------------------
section('参照アセット（assets/）の実在');
const assetPaths = [...html.matchAll(/(?:src|href)\s*=\s*"((?:\.\/)?assets\/[^"]+)"/gi)]
  .map((m) => m[1].replace(/^\.\//, ''));
const uniqueAssets = [...new Set(assetPaths)];
if (uniqueAssets.length === 0) {
  ok('assets/ への参照なし（チェック対象なし）');
} else {
  for (const rel of uniqueAssets) {
    existsSync(join(ROOT, rel)) ? ok(`${rel} が存在`) : ng(`${rel} が参照されていますが見つかりません`);
  }
}

// ---------------------------------------------------------------------------
// 5. HTML 基本健全性
// ---------------------------------------------------------------------------
section('HTML 基本健全性');
html.length > 1000 ? ok(`index.html は ${html.length.toLocaleString()} bytes（非空）`) : ng('index.html が小さすぎます');
count(html, '<html') === count(html, '</html>') && count(html, '<html') >= 1
  ? ok('<html> の開閉が対応')
  : ng('<html> の開閉が不一致');
/<body[\s>]/.test(html) && /<\/body>/.test(html)
  ? ok('<body> が存在')
  : ng('<body> が見つかりません');

// ---------------------------------------------------------------------------
// 結果
// ---------------------------------------------------------------------------
console.log('\n' + '='.repeat(48));
if (failures === 0) {
  console.log('✅ すべての検査に合格しました。デプロイ可能です。');
  process.exit(0);
} else {
  console.log(`❌ ${failures} 件の検査に失敗しました。デプロイを中止します。`);
  process.exit(1);
}
