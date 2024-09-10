<!-- Used Currency, Float, Int, Percent -->
<script setup>
import { computed, onMounted, onUpdated, ref, useSlots, watch } from "vue";

const props = defineProps(["df", "value", "read_only"]);
const slots = useSlots();
const fieldWrapper = ref(null);

const in_preview = computed(() => !!slots.actions); // is inside preview

const emit = defineEmits(["update:modelValue"]);

// Create a <fieldWrapper> element dynamically
const createInput = (wrapper) => {
	let df = props.df;
	df = { ...df, hidden: 0 };
	if (props.read_only || in_preview.value) {
		df.read_only = true;
	} else {
		df.onchange = () => {
			emit("update:modelValue", field.get_value());
		};
	}

	const field = frappe.ui.form.make_control({
		df: df,
		parent: wrapper,
		render_input: true,
		value: props.value,
		only_input: true,
	});
};

const refreshInput = () => {
	if (fieldWrapper.value) {
		fieldWrapper.value.innerHTML = "";
		createInput(fieldWrapper.value);
	}
};

onUpdated(refreshInput);
onMounted(refreshInput);
watch(() => props.df.configuration, refreshInput);
</script>

<template>
	<div class="control frappe-control" :class="{ editable: in_preview }">
		<!-- label -->
		<div v-if="in_preview" class="field-controls">
			<slot name="label" />
			<slot name="actions" />
		</div>
		<div v-else class="control-label label" :class="{ reqd: df.reqd }">{{ df.label }}</div>

		<!-- input -->
		<div :style="{ pointerEvents: in_preview ? 'none' : 'auto' }" ref="fieldWrapper" />

		<!-- description -->
		<div v-if="df.description" class="mt-2 description" v-html="df.description" />
	</div>
</template>
