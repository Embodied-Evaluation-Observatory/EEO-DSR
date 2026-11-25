# Phase 0 披露度普查 2026-11-26

本集合 0 项 FAIL 不代表卡片自洽；S1 在 20 张卡上全部不可判。

本集合 20 张卡片中 0 张至少一项 FAIL，20 张至少一项 MISSING；两项都有的 0 张。

本目录字段由 `tools/screen_cards.py` 自动解析自钉住的页面字节；**没有人工转录**。每张卡片的原始页面字节存在 `pages/`，其哈希（`page_sha256`）与结构化字段哈希（`card_sha256`）见 `cards.csv`。

## 集合级可判率

| 项 | 可判 (PASS+FAIL)/m | 可判率 | 判定 |
|---|---:|---:|---|
| S1 | 0/20 | 0% | 不可判 |
| S2 | 0/20 | 0% | 不可判 |
| S3 | 0/20 | 0% | 不可判 |
| S4 | 12/20 | 60% | 无可区分信号 |
| S5 | 0/20 | 0% | 不可判 |
| S6 | 0/20 | 0% | 不可判 |

某项 100% MISSING 时判为不可判，不计入通过。全部行同构时，声明本集合上无区分信号。
可判率是集合上的分布，不是对单张卡片的评级。

## 逐项分布

S1 PASS 0 / FAIL 0 / MISSING 20；S2 PASS 0 / FAIL 0 / MISSING 20；S3 PASS 0 / FAIL 0 / MISSING 20；S4 PASS 12 / FAIL 0 / MISSING 8；S5 PASS 0 / FAIL 0 / MISSING 20；S6 PASS 0 / FAIL 0 / MISSING 20

S1 测的是分场景计数之和与声明总数；卡片没有分场景计数时，S1 记 MISSING，不是 FAIL。
S2 只有在卡片声明 `frames_per_episode` 或 `seconds_per_episode` 且与重算一致时才 PASS；只给条数、帧数与 fps 不够。

`manifest.sha256` 钉住 `manifest.json`；`manifest.json` 列出输入与三个输出文件的哈希。

- `bridge-data-project`：https://rail-berkeley.github.io/bridgedata/  page `9be7a758ab24782955a6fa4145bbed80527671939e4f40dff70e22ee9b69c580`  card `1a0c95c76df1ee90473eed4a59007534a998d3d89e235ee3bff03fc3ac5ae9b4`
- `calvin`：https://raw.githubusercontent.com/mees/calvin/main/README.md  page `ade3f2d224f5f299be858681ab117524b6457e371963718518718529b2fd12f2`  card `47be0a4b032302a7c6e8bd558e0895fb861bbe47825250dbc2fca4f63037182f`
- `droid-project`：https://droid-dataset.github.io/  page `48e7283e8fa77441818ac74f833e7b2529b78ba750cd3808750fc63a45e84b20`  card `36e71610faa9b010a7d0871bfdfb7394e840e8ba381379d8b17dbc2344b853c9`
- `lerobot/aloha_mobile_cabinet`：https://huggingface.co/datasets/lerobot/aloha_mobile_cabinet/raw/main/README.md  page `e10aecfc8b0ca9c62a3879b8e8e35d7b5b81ecabca0352bdf27a6e38ff6e788e`  card `1081cb561268e8ee07573604dca9cd7ddfd1b44ce9371733ad7eb6b8a4922511`
- `lerobot/berkeley_cable_routing`：https://huggingface.co/datasets/lerobot/berkeley_cable_routing/raw/main/README.md  page `5e7c238aba09654b57af7300cca85570c4cb21f161684023671321913a207f8e`  card `3076d90943d2ce2c5cdd68a6cf21e705f2dfbd256f2d0b9d844e9b705781a318`
- `lerobot/berkeley_gnm_sac_son`：https://huggingface.co/datasets/lerobot/berkeley_gnm_sac_son/raw/main/README.md  page `2464148b306ebe9b1c1597e7c09a283d5ab3e86bc9a6313b91db2d17b7ff8416`  card `4c4cbbc27419d95ca85936bcbff596afd22d81c6350597e24506c0b964bb5c98`
- `lerobot/jaco_play`：https://huggingface.co/datasets/lerobot/jaco_play/raw/main/README.md  page `320ce6e05ea213e021869d50df73d80c5fbecbc61692a90b1fac51cddfe1ef6e`  card `91dd8aa6e2e95530a0ffa96612037caade1dc568ff372779a65aec299190b828`
- `lerobot/libero`：https://huggingface.co/datasets/lerobot/libero/raw/main/README.md  page `5a76b1cdc8b0012a048eea96bce7e0a4367537aa3c1acac3a19aae722c1debe6`  card `2754613074d693227a1e9cae9046da8f1f5d87d5a3e9e807843a44ff324aaa46`
- `lerobot/nyu_rot_dataset`：https://huggingface.co/datasets/lerobot/nyu_rot_dataset/raw/main/README.md  page `979b2259449eef49ea2e593f20951fde5aa8e8f636a7c08dacfed5101dcf5554`  card `67767f2b6f3398ca4ffa8706530e65307c0ccd1dc138ef41104638bc9fd0542e`
- `lerobot/pusht`：https://huggingface.co/datasets/lerobot/pusht/raw/main/README.md  page `246e94b68f204bfcd05bb32e23631c3316b8de6152d7a85e693d4455540ef72f`  card `9d568624fe865e98a7683c2f98057406fa342ccb0295659885e4bd4577fe20db`
- `lerobot/roboturk`：https://huggingface.co/datasets/lerobot/roboturk/raw/main/README.md  page `f37e4f6262f49c7e2068e6d51abd22761765d881ab2442b3942297d92aa42c3a`  card `324da70d0ebab1231165edd82d99c47fa28ac609cc75578a5983e7fb69ceae01`
- `lerobot/stanford_hydra_dataset`：https://huggingface.co/datasets/lerobot/stanford_hydra_dataset/raw/main/README.md  page `fb71c6f20843000c236b68afb849670fb02e221c12e184c0f46ddca14e2e16fb`  card `12f7a91b860ac6d46ca7e12c9d21236145f5c7170db7ace392b893a14bc75250`
- `lerobot/svla_so101_pickplace`：https://huggingface.co/datasets/lerobot/svla_so101_pickplace/raw/main/README.md  page `74a5ac3cf6de11b315eb4d01b1ce0e6250782fa809183f76b56aaa3d26a63d76`  card `9eea18df07a897e91dd994fbb82e322d2dc651b1e3f69e303e8648770e6e30fb`
- `lerobot/taco_play`：https://huggingface.co/datasets/lerobot/taco_play/raw/main/README.md  page `38f678c2a6722d764283c6822cfa7f3904706e93e7340058e84352479d87e678`  card `0e3a7d72162f1daa2f4bdcacde1d65b51b000cfbe5aa2e690e1e05e621a8ea19`
- `lerobot/xarm_lift_medium`：https://huggingface.co/datasets/lerobot/xarm_lift_medium/raw/main/README.md  page `0650cf886bcb149939b686bdd38f0ba5f683076888808481c6b33257f117eb79`  card `86ab2d839def26dd1dc8468743d556b4a9cfdad0b70dc1a082d56033a5478cd0`
- `libero-project`：https://libero-project.github.io/intro.html  page `98ab6d9317aa3115f17b35fc54cfd6c209b0387f82741baf6a600a0f54d38faf`  card `0b781e25867e98db9a1b3ad43e8a2b7b2cb6f6903280cd3f4b4f0f735512134a`
- `maniskill`：https://raw.githubusercontent.com/haosulab/ManiSkill/main/README.md  page `304da9c2fdf69bf8944e1293a5c1bf146c434b2e6acd7604a46b3cfbfdfac10f`  card `5746a953627b2f2ca530f65bb831bfae65142ada5f347530a92fd5f19cc3b801`
- `openx-project`：https://robotics-transformer-x.github.io/  page `cfc69260794ec363d14bf899ac9ec38013c09727215a52a037add457aeb4b02b`  card `58c22b4894b81f13c878307b3fc72cd9357afc0cc3e22fe6b8d48d9df62a7475`
- `robocasa`：https://raw.githubusercontent.com/robocasa/robocasa/main/README.md  page `e8a421497dbe714ad912dae9d98c0f0cb6d17685f9a4be5537193419f75abea8`  card `9b253d9e89b03c89fc638ced5c5268c608d10ec9344f9c2fd291102f5ed208f7`
- `robomimic`：https://raw.githubusercontent.com/ARISE-Initiative/robomimic/master/README.md  page `edb7d231bfcfec74559cec7e2c950b32317f1488d8898b27798ac7b155f5aec9`  card `701cd8131c19a6cf41be29a9f86a68a5531cbecc6a1e1b5c8b2ba5629f186a9f`

本页只报告披露与算术，不构成核验结论，不说明语料可用性。