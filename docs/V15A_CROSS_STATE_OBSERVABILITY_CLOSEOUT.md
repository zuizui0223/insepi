# V15a cross-state observability: pre-field programming closeout

## 結論

実測前のプログラミング目標は完了した。V14bで固定した6つの物理状態と
588万worldを変更せず、V15の独立な観察支持 `O` を11条件で直交させた。
得られた6468万の解釈では、観察支持が劣化した条件は理由付きU、観察不能
条件はcensoredであり、いずれも対象不在へ変換されない。

これは「棄却・保留を性能上の欠陥として一括処理せず、観察条件に条件づけた
推定対象として保持する」という主張のclosed-world／software-semanticな実証
である。フィールド性能や検出確率の実証ではない。

## 固定した宇宙

- 物理状態は `baseline`、`target_only`、`nuisance_only`、
  `target_coupled`、`target_nuisance_superposed`、
  `target_nuisance_coupled` の6つである。
- 対象 `T` は局在したentry-dwell-exit過程、対象外 `N` は対象相互作用に
  条件づけられない外生時空間過程である。
- 観察支持 `O` は物理原因ではなく、同じ物理世界を観察できたかを表す独立層
  である。
- V14b observer、family-wise alpha `0.05`、nuisance threshold
  `4.33898869355123e-06` は不変更である。

## 一回目の固定結果

測定前コミットは `5e8163891cd5f358f522cc0f9e99c6ff3c1318b4`、結果payloadの
SHA-256は
`4346304cbef50a0e68ed57c2ae45356ed118b7a8713d08bf557ce7e1f4f185a1`
である。親worldは再生成していない。

| 独立O条件 | profile数 | 最終処理 | unsafe forced-binaryのFN率 |
|---|---:|---|---:|
| observable | 1 | V14b state/reasonをそのまま保持 | 0.3569 |
| compromised | 5 | `U_observation_compromised` | 1.0 |
| unobservable | 5 | `censored_observation_unavailable` | 1.0 |

観察不能の2940万解釈はすべてcensored、劣化した2940万解釈はすべて理由付き
Uとなった。静穏なbaselineも例外ではなく、observableならbaseline、
compromisedならU、unobservableならcensoredとなった。したがって「静か」と
「観察できない」は同義ではない。

設計した11 profileを等しく重みづけしたunsafe forced-binary比較では、対象が
存在する4312万解釈のうち4059万9048件を不在へ強制し、FN率は
`0.9415363636363636` となる。この値は設計格子上の比較であり、O条件の野外頻度
を表さない。partial-identification幅はobservableで
`0.4835690476190476`、compromisedとunobservableで各`1.0`、格子等重みで
`0.9530517316017316` だった。

## 保持した不整合と停止

最初の2回の実行呼び出しは結果生成前に停止した。原因は、親のregime meanを
整数world数へ戻せる、また厳密に1へ合計される、という実装上の仮定だった。
どちらも結果ファイルを作らず、observer出力を再生成していない。停止履歴は
`benchmarks/v15a_cross_state_observability_preflight_history.json` に保持した。

親summaryの `target_nuisance_coupled` には状態率合計に
`5.102040816495901e-07` の残差があり、global baseline率と6 regime平均にも
`8.503401358050944e-08` の差がある。V15aはこれを正規化・整数化・修復せず、
入力監査値として結果へ残す。

## 主張できる範囲

支持されるのは、固定したclosed-worldでは同一の物理状態でも観察支持により
最終の認識状態が変わり、Uとcensorshipを不在へ強制すると誤陰性が観察条件の
関数になる、ということまでである。

次は支持されない。

- 野外でのO条件の頻度、検出確率、accuracy
- 現行の0.70／0.30 support thresholdの野外妥当性
- 虫の目的・意図の認識
- あらゆるbinary classifierに対する優越性
- すべての棄却が望ましい、またはmodel inadequacyが棄却を生まないという主張

したがって、この成果は「実測前のプログラミング成果」として閉じる。次の科学
ゲートは、別契約の実pixel／support truthによる測定であり、この結果を見た後に
V14b/V15aを調整することではない。
