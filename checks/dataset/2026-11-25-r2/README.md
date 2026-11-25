# Phase 0 初筛 2026-11-25

本集合 12 张卡片中 0 张至少一项 FAIL，12 张至少一项 MISSING；两项都有的 0 张。

本目录字段由 `tools/screen_cards.py` 自动解析自钉住的页面字节；**没有人工转录**。每张卡片的原始页面字节存在 `pages/`，其哈希（`page_sha256`）与结构化字段哈希（`card_sha256`）见 `cards.csv`。

S1 测的是分场景计数之和与声明总数；卡片没有分场景计数时，S1 记 MISSING，不是 FAIL。
MISSING 与 FAIL 分开汇总：前者是字段没公布，后者是已公布的数算不平。

逐项分布：S1 PASS 0 / FAIL 0 / MISSING 12；S2 PASS 12 / FAIL 0 / MISSING 0；S3 PASS 0 / FAIL 0 / MISSING 12；S4 PASS 12 / FAIL 0 / MISSING 0；S5 PASS 0 / FAIL 0 / MISSING 12；S6 PASS 0 / FAIL 0 / MISSING 12

`manifest.sha256` 钉住 `manifest.json`；`manifest.json` 列出输入与三个输出文件的哈希。

- `lerobot/aloha_mobile_cabinet`：https://huggingface.co/datasets/lerobot/aloha_mobile_cabinet/raw/main/README.md  page `e10aecfc8b0ca9c62a3879b8e8e35d7b5b81ecabca0352bdf27a6e38ff6e788e`  card `85df1caa099edab78e8520886d2d0dd6345422971d195369d1cb5c36145d2231`
- `lerobot/berkeley_cable_routing`：https://huggingface.co/datasets/lerobot/berkeley_cable_routing/raw/main/README.md  page `5e7c238aba09654b57af7300cca85570c4cb21f161684023671321913a207f8e`  card `f3830e1c1ca81e3fbb4598418a689f1a4401c86f94acf446aa3d6eac6a5da2eb`
- `lerobot/berkeley_gnm_sac_son`：https://huggingface.co/datasets/lerobot/berkeley_gnm_sac_son/raw/main/README.md  page `2464148b306ebe9b1c1597e7c09a283d5ab3e86bc9a6313b91db2d17b7ff8416`  card `554f9d2f24706ab32f634347a8b2f52db0875ee08507aebc2c3fe7d7f266544e`
- `lerobot/jaco_play`：https://huggingface.co/datasets/lerobot/jaco_play/raw/main/README.md  page `320ce6e05ea213e021869d50df73d80c5fbecbc61692a90b1fac51cddfe1ef6e`  card `9c2b404ac7753e35ca10f0c7d52fe529e09488b4a07a31d03749789640766da6`
- `lerobot/libero`：https://huggingface.co/datasets/lerobot/libero/raw/main/README.md  page `5a76b1cdc8b0012a048eea96bce7e0a4367537aa3c1acac3a19aae722c1debe6`  card `699a251c88578586a5296161d6aaae8364df6b5b9c11fb8595753c2f22c65365`
- `lerobot/nyu_rot_dataset`：https://huggingface.co/datasets/lerobot/nyu_rot_dataset/raw/main/README.md  page `979b2259449eef49ea2e593f20951fde5aa8e8f636a7c08dacfed5101dcf5554`  card `cf07dd4c18904b2869e6d0e1cf0bc927c96053fb21302eaa87f0f03173f429c2`
- `lerobot/pusht`：https://huggingface.co/datasets/lerobot/pusht/raw/main/README.md  page `246e94b68f204bfcd05bb32e23631c3316b8de6152d7a85e693d4455540ef72f`  card `9f77fb364f1b1ed387c1283a7f94582dc2fcafd3e4d997dc209e179c4aa845c7`
- `lerobot/roboturk`：https://huggingface.co/datasets/lerobot/roboturk/raw/main/README.md  page `f37e4f6262f49c7e2068e6d51abd22761765d881ab2442b3942297d92aa42c3a`  card `9985d97ae5f090cb084e35b9af3a0e6fddd1c31c361c52da88a21cc134b94766`
- `lerobot/stanford_hydra_dataset`：https://huggingface.co/datasets/lerobot/stanford_hydra_dataset/raw/main/README.md  page `fb71c6f20843000c236b68afb849670fb02e221c12e184c0f46ddca14e2e16fb`  card `7d9057cc996a6a3d484809a637013c12e435347e482e9ee0175a474f8f997c1c`
- `lerobot/svla_so101_pickplace`：https://huggingface.co/datasets/lerobot/svla_so101_pickplace/raw/main/README.md  page `74a5ac3cf6de11b315eb4d01b1ce0e6250782fa809183f76b56aaa3d26a63d76`  card `a8729a28aa9901d35b15be8ea5da86547bc1cffd77b1ac555d37e980ed9daa28`
- `lerobot/taco_play`：https://huggingface.co/datasets/lerobot/taco_play/raw/main/README.md  page `38f678c2a6722d764283c6822cfa7f3904706e93e7340058e84352479d87e678`  card `c54559942784e1c5d064e8199dbefeb7d96c0c745fced2a3259f3ce5b0990905`
- `lerobot/xarm_lift_medium`：https://huggingface.co/datasets/lerobot/xarm_lift_medium/raw/main/README.md  page `0650cf886bcb149939b686bdd38f0ba5f683076888808481c6b33257f117eb79`  card `ad8962560e5f5a664e64b25560f2333c89492d52cffcd5b522ff9dea3709e8ae`

本页只做卡片算术，不构成核验结论，不说明语料可用性。