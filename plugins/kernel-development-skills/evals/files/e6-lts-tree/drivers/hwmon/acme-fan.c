// SPDX-License-Identifier: GPL-2.0-only
/*
 * Acme fan controller
 */

#include <linux/io.h>
#include <linux/module.h>
#include <linux/of.h>
#include <linux/platform_device.h>

#define ACME_FAN_TACH	0x10

struct acme_fan {
	void __iomem *base;
	u32 rpm;
};

static int acme_fan_probe(struct platform_device *pdev)
{
	struct acme_fan *fan;

	fan = devm_kzalloc(&pdev->dev, sizeof(*fan), GFP_KERNEL);
	if (!fan)
		return -ENOMEM;

	fan->base = devm_platform_ioremap_resource(pdev, 0);
	if (IS_ERR(fan->base))
		return PTR_ERR(fan->base);

	platform_set_drvdata(pdev, fan);
	return 0;
}

static int acme_fan_remove(struct platform_device *pdev)
{
	return 0;
}

static const struct of_device_id acme_fan_of_match[] = {
	{ .compatible = "acme,fan" },
	{ }
};
MODULE_DEVICE_TABLE(of, acme_fan_of_match);

static struct platform_driver acme_fan_driver = {
	.probe = acme_fan_probe,
	.remove = acme_fan_remove,
	.driver = {
		.name = "acme-fan",
		.of_match_table = acme_fan_of_match,
	},
};
module_platform_driver(acme_fan_driver);

MODULE_DESCRIPTION("Acme fan controller driver");
MODULE_LICENSE("GPL");
