{{- define "persistent-petitioner.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- define "persistent-petitioner.fullname" -}}
{{- default .Release.Name .Values.fullnameOverride | default (include "persistent-petitioner.name" .) | trunc 63 | trimSuffix "-" }}
{{- end }}
