## ADDED Requirements

### Requirement: 固定ch32funのhelperとデバイス仕様の照合

固定submoduleのch32funの関数やhelperの処理が、対象デバイスの資料や実測と合わない疑いがある場合は、実機で挙動を確かめて記録しなければならない（SHALL）。サンプルでの使用・回避の判断と根拠を残さなければならない（SHALL）。submoduleは変更してはならない（SHALL NOT）。

#### Scenario: funAnalogInitを002/006で使う
- **WHEN** `funAnalogInit()` と `funAnalogRead()` を002または006で実行する
- **THEN** 初期化が戻るか、変換結果が得られるかを、デバイスごとに実測として記録する
- **AND** 問題がある場合、サンプルは直接レジスタを操作する現在の実装を維持し、上流へ報告するかを別に判断する

#### Scenario: helperのコメントと実測が異なる
- **WHEN** サンプルのコメントがhelperの挙動（例: STOPの報告の有無）を説明している
- **THEN** 002/006でその挙動を観測し、コメントを観測に合わせる
