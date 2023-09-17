using System;
using System.Collections.Generic;

namespace com.adjust.sdk
{
    public class AdjustAdRevenue
    {
        internal string source;
        internal double? revenue;
        internal string currency;
        internal int? adImpressionsCount;
        internal string adRevenueNetwork;
        internal string adRevenueUnit;
        internal string adRevenuePlacement;
        internal List<string> partnerList;
        internal List<string> callbackList;

        public AdjustAdRevenue(string source)
        {
            this.source = source;
        }

        public void setRevenue(double amount, string currency)
        {
            this.revenue = amount;
            this.currency = currency;
        }

        public void setAdImpressionsCount(int adImpressionsCount)
        {
            this.adImpressionsCount = adImpressionsCount;
        }

        public void setAdRevenueNetwork(string adRevenueNetwork)
        {
            this.adRevenueNetwork = adRevenueNetwork;
        }

        public void setAdRevenueUnit(string adRevenueUnit)
        {
            this.adRevenueUnit = adRevenueUnit;
        }

        public void setAdRevenuePlacement(string adRevenuePlacement)
        {
            this.adRevenuePlacement = adRevenuePlacement;
        }

        public void addCallbackParameter(string key, string value)
        {
            if (callbackList == null)
            {
                callbackList = new List<string>();
            }
            callbackList.Add(key);
            callbackList.Add(value);
        }

        public void addPartnerParameter(string key, string value)
        {
            if (partnerList == null)
            {
                partnerList = new List<string>();
            }
            partnerList.Add(key);
            partnerList.Add(value);
        }
    }
}