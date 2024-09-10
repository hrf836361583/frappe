<script setup>
import { useSlots } from "vue";

const props = defineProps(["df", "value", "read_only", "modelValue"]);
let emit = defineEmits(["update:modelValue"]);
let slots = useSlots();
</script>

<template>
	<div class="control" :class="{ editable: slots.label }">
		<!-- label -->
		<div v-if="slots.label" class="field-controls">
			<slot name="label" />
			<slot name="actions" />
		</div>
		<div v-else class="control-label label">{{ __(df.label) }}</div>

		<div v-if="df.description" class="mt-2" v-html="df.options"></div>

		<!-- description -->
		<div v-if="df.description" class="mt-2 description" v-html="df.description"></div>
	</div>
</template>
