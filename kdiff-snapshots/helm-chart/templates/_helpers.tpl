{{/*
*/}}
{{- define "kdiff-snapshots.containerVolumeMounts" -}}
{{- if or (or .Values.steampipeConfig .Values.steampipeSecretCredentials) .Values.initDbSqlScripts }}
volumeMounts:
  {{- range $key, $value := .Values.steampipeConfig }}
  - name: steampipe-config-volume
    mountPath: /home/steampipe/.steampipe/config/{{ $key }}
    subPath: {{ $key }}
  {{- end }}
  {{- range $config := .Values.steampipeSecretCredentials }}
  - name: steampipe-credentials-volume
    mountPath: /home/steampipe/{{ $config.directory }}/{{ $config.filename }}
    subPath: {{ $config.filename }}
  {{- end }}
  {{- range $key, $value := .Values.initDbSqlScripts }}
  - name: steampipe-initdb-volume
    mountPath: /home/steampipe/initdb-sql-scripts/{{ $key }}
    subPath: {{ $key }}
  {{- end }}
{{- else }}
volumeMounts: []
{{- end }}
{{- end }}


{{- define "kdiff-snapshots.containerVolumes" -}}
{{- if or (or .Values.steampipeConfig .Values.steampipeSecretCredentials) .Values.initDbSqlScripts }}
volumes:
  {{- if or .Values.steampipeConfig }}
  - name: steampipe-config-volume
    configMap:
      name: {{ include "kdiff-snapshots.fullname" . }}-steampipe-config
      optional: true
      items:
      {{- range $key, $value := .Values.steampipeConfig }}
      - key: {{ $key }}
        path: {{ $key }}  # same as subPath
      {{- end }}
  {{- end }}
  {{- if or .Values.steampipeSecretCredentials }}
  - name: steampipe-credentials-volume
    secret:
      secretName: {{ include "kdiff-snapshots.fullname" . }}-steampipe-creds
      optional: true
      items:
      {{- range $config := .Values.steampipeSecretCredentials }}
      - key: {{ $config.name }}
        path: {{ $config.filename }}  # same as subPath
      {{- end }}
  {{- end }}
  {{- if or .Values.initDbSqlScripts }}
  - name: steampipe-initdb-volume
    configMap:
      name: {{ include "kdiff-snapshots.fullname" . }}-initdb-sql-files
      optional: true
      items:
      {{- range $key, $value := .Values.initDbSqlScripts }}
      - key: {{ $key }}
        path: {{ $key }}  # same as subPath
      {{- end }}
  {{- end }}
{{- else }}
volumes: []
{{- end }}
{{- end }}


{{/*
Expand the name of the chart.
*/}}
{{- define "kdiff-snapshots.name" -}}
{{- .Values.nameOverride | default .Chart.Name }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "kdiff-snapshots.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "kdiff-snapshots.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "kdiff-snapshots.labels" -}}
helm.sh/chart: {{ include "kdiff-snapshots.chart" . }}
{{ include "kdiff-snapshots.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "kdiff-snapshots.selectorLabels" -}}
app.kubernetes.io/name: {{ include "kdiff-snapshots.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "kdiff-snapshots.serviceAccountName" -}}
{{- default (include "kdiff-snapshots.fullname" .) (.Values.serviceAccount).name }}
{{- end }}
