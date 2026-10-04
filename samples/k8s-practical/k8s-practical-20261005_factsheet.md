# ファクトシート：Kubernetes 実務入門（サンプル）

- 教材ID：`k8s-practical-20261005`
- 対象バージョン：Kubernetes v1.34 系の公式ドキュメント（2026-10 時点）
- 作成日：2026-10-05

| ID | 主張（1行） | 出典URL | 信頼度 | 使用箇所 |
|---|---|---|---|---|
| F-001 | Pod は Kubernetes で作成・管理できる最小のデプロイ単位で、1つ以上のコンテナのグループである | https://kubernetes.io/docs/concepts/workloads/pods/ | S | 1章 Kubernetes の基本オブジェクト ／ 1.1 Pod |
| F-002 | 同じ Pod のコンテナはストレージとネットワークを共有し、localhost で互いに通信できる | https://kubernetes.io/docs/concepts/workloads/pods/ | S | 1章 Kubernetes の基本オブジェクト ／ 1.1 Pod |
| F-003 | Pod は使い捨て（比較的短命）を前提にしており、Pod 自体は自己修復しない。通常は直接作らず Deployment などのワークロードリソースで作る | https://kubernetes.io/docs/concepts/workloads/pods/ | S | 1章 Kubernetes の基本オブジェクト ／ 1.1 Pod |
| F-004 | Deployment は ReplicaSet を作り、ReplicaSet が指定数の Pod を維持する | https://kubernetes.io/docs/concepts/workloads/controllers/deployment/ | S | 1章 Kubernetes の基本オブジェクト ／ 1.2 Deployment と ReplicaSet<br>2章 Pod のトラブルシューティング ／ 2.2 describe と logs で原因を探す |
| F-005 | Deployment のロールアウトは .spec.template が変わったときだけ始まり、新しい ReplicaSet を作って Pod を順に入れ替える（既定の RollingUpdate）。スケールではロールアウトは起きない | https://kubernetes.io/docs/concepts/workloads/controllers/deployment/ | S | 1章 Kubernetes の基本オブジェクト ／ 1.2 Deployment と ReplicaSet |
| F-006 | kubectl rollout undo で Deployment を前のリビジョンに戻せる | https://kubernetes.io/docs/concepts/workloads/controllers/deployment/ | S | 1章 Kubernetes の基本オブジェクト ／ 1.2 Deployment と ReplicaSet |
| F-007 | Pod の phase は Pending・Running・Succeeded・Failed・Unknown の5つ | https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/ | S | 2章 Pod のトラブルシューティング ／ 2.1 Pod の状態を読む |
| F-008 | Pending はクラスタに受け入れられたがコンテナがまだ動く状態にない phase で、スケジュール待ちやイメージのダウンロード中を含む | https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/ | S | 2章 Pod のトラブルシューティング ／ 2.1 Pod の状態を読む |
| F-009 | CrashLoopBackOff は phase ではなく、コンテナが起動と異常終了を繰り返し、kubelet が待ち時間を延ばしながら再起動している状態 | https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/ | S | 2章 Pod のトラブルシューティング ／ 2.1 Pod の状態を読む |
| F-010 | イメージを取得できないとき、Pod は ImagePullBackOff になり取得を再試行する。イメージ名の誤りや非公開レジストリの認証情報不足などで起こる | https://kubernetes.io/docs/concepts/containers/images/ | S | 2章 Pod のトラブルシューティング ／ 2.1 Pod の状態を読む |
| F-011 | kubectl describe pod は Pod の詳細と Events を表示する。Pending のまま進まない Pod は、スケジューラのメッセージを Events で確認する | https://kubernetes.io/docs/tasks/debug/debug-application/debug-pods/ | S | 2章 Pod のトラブルシューティング ／ 2.2 describe と logs で原因を探す |
| F-012 | Pending のまま進まない Pod の多くは、CPU やメモリの不足でノードに割り当てられていない | https://kubernetes.io/docs/tasks/debug/debug-application/debug-pods/ | S | 2章 Pod のトラブルシューティング ／ 2.2 describe と logs で原因を探す |
| F-013 | kubectl logs の --previous（-p）は、前回終了したコンテナのログを表示する | https://kubernetes.io/docs/reference/kubectl/generated/kubectl_logs/ | S | 2章 Pod のトラブルシューティング ／ 2.2 describe と logs で原因を探す |
| F-014 | kubectl get pods で Pod の一覧と状態を表示できる | https://kubernetes.io/docs/reference/kubectl/quick-reference/ | S | 2章 Pod のトラブルシューティング ／ 2.1 Pod の状態を読む |
| F-015 | kubectl rollout status で Deployment のロールアウトの状況を確認できる | https://kubernetes.io/docs/concepts/workloads/controllers/deployment/ | S | 1章 Kubernetes の基本オブジェクト ／ 1.2 Deployment と ReplicaSet |
| F-016 | phase の意味：Running は少なくとも1つのコンテナが動いている、Succeeded はすべてのコンテナが正常終了し再起動しない、Failed はすべてのコンテナが終了し少なくとも1つが失敗、Unknown は状態を取得できない | https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/ | S | 2章 Pod のトラブルシューティング ／ 2.1 Pod の状態を読む |
| F-017 | kubectl get pods の RESTARTS 列はコンテナの再起動回数を示す | https://kubernetes.io/docs/tasks/debug/debug-application/debug-pods/ | S | 2章 Pod のトラブルシューティング ／ 2.1 Pod の状態を読む |
| F-018 | コンテナが標準出力・標準エラー出力に書いたログは kubectl logs で見られる | https://kubernetes.io/docs/concepts/cluster-administration/logging/ | S | 2章 Pod のトラブルシューティング ／ 2.2 describe と logs で原因を探す |
