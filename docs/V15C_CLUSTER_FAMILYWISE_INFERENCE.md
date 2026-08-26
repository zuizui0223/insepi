# V15c cluster family-wise inference

## 現在地

V15cはV15bがtruth開封時に出した十分統計だけを読み、raw truth、予測ledger、frameへ
戻らずに推論する。repository内のanalysis planは実行不能templateであり、実測結果は
含まれていない。

## 推定対象

比較は `target_plus_nuisance_without_support_gate` と
`full_direct_coupled_target_nuisance_observability_triad` に固定する。両者は同じT/C/Nを
使うため、差は独立したobservation-support gateとprocess-preserving triad decisionで
ある。

family-wise αは凍結済みの0.05のまま、次の4仮説へBonferroniで配分する。

1. resolved visitに対する偽不在率が最低幅以上減る。
2. observable resolved visitのcandidate recallが凍結margin内で非劣性となる。
3. truth-resolved unobservable windowをcensorとして回収する率が下限以上となる。
4. truth-resolved observable windowを誤ってcensorする率が上限以下となる。

4件すべてをactual `recording_date_local × physical_scene_code` cluster単位のpaired
bootstrapで評価する。frameもwindowも独立反復にはしない。4件すべてが通った場合だけ
familyをsupportedとする。十分なclusterまたは分母がなければ0率を代入せず、
`not_evaluable` を保持する。

## 実測前に別途凍結する値

`v15c_cluster_analysis_plan_TEMPLATE.json` をdefaultとして使ってはならない。held-out
inputを読む前に、sample-size planと整合するcluster数・各分母の最低数、および4つの
科学的claim thresholdを実値で固定する。そのcanonical SHA-256をV15b measurement
freezeの `cluster_analysis_plan_sha256` に入れる。

runnerはこのhash連鎖が一致しない限りV15b resultを読まずに停止する。結果が
`not_supported` または `not_evaluable` でも閾値変更や再実行で救済しない。

## claim ceiling

将来familyがsupportedでも、主張できるのは標本化されたday × scene母集団に対する
宣言済みobservation-support claimまでである。censoredを生物学的不在とする主張、
普遍的優越性、送粉有効性は含まない。
