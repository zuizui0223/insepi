# V15b held-out measurement gate

## 現在地

V15bは、実pixel由来のT/C/N/O component ledgerを受け取った後、held-out truthを
開く前に5方式の予測を固定するためのsoftware gateである。V14b/V15aの結果、
observer、family-wise alphaは変更しない。

repositoryにあるmeasurement freezeはtemplateであり実行不能である。実データ、
実予測、field resultは含まれていない。

## 二段階の情報境界

### 1. Blinded prediction and commitment

`scripts/v15b_predict_and_commit.py` は次だけを読む。

- held-out inputを読む前に完成したmeasurement freeze
- truth-freeなdirect target、coupled response、target-link、nuisance risk
- primary-stream support measurements
- protected random-audit選択
- truth内容を含まないseal receipt

出力は全5方式のprediction ledgerと、そのcanonical SHA-256 commitmentである。
biological、coupling、nuisance、support truthは入力できない。各rowのkey setも固定し、
余分なtruth fieldをfail-closedで拒否する。

### 2. Post-commitment truth join

`scripts/v15b_evaluate_locked.py` は次の順序を強制する。

1. measurement freezeを検証する。
2. prediction ledgerをpre-unseal commitmentと照合する。
3. truth fileのbytesを、prediction前に作られたseal receiptと照合する。
4. ここまで通過してからtruth JSONを開く。
5. 独立にadjudicateされた4層truthをwindow IDとclip SHAでjoinする。
6. 固定済みwindow metricsを5方式で比較する。

未解決truthは不在へ変換せず、unobservable supportはcensoredのまま保持する。

## 修正した世代間不整合

V15の `FULL_TRIAD` は旧 `ObservationTriadPolicy` ではなく、V14bで確定した
`ProcessPreservingObservationTriadPolicy` を使う。したがって、target evidenceと
nuisance evidenceがともに高くOがobservableなworldは、正当なsuperpositionとして
positive candidateを保持し、同時にaudit対象となる。

## 現在のclaim ceiling

実装済みなのは、no-peek順序、prediction/truthのhash binding、4層truth join、
window-level descriptive metrics、実際の
`recording_date_local × physical_scene_code` cluster inventoryまでである。

family-wise alpha `0.05` はmanifestで保持するが、この世代が実行するfamily-wise
hypothesis testは0件である。cluster bootstrap、sample-size/powerに基づく判定、
field accuracy claimは次世代のfreezeなしには許可しない。frameを独立反復として
扱うことも禁止する。

## 実データ前に必要な別freeze

templateを実行可能にするには、少なくとも次をheld-out input access前に埋め、別の
committed manifestとして固定する必要がある。

- exact target/nuisance observer commits
- coupled-route definition SHA-256
- support measurement profile SHA-256
- sample-size plan SHA-256
- cluster-analysis plan SHA-256
- developmentで決めたT/N/O thresholds
- missing-data rule

このfreezeがない限りrunnerは停止する。template値を暗黙にdefaultとして使わない。
