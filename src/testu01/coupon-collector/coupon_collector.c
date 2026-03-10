// =================================================================================================
//! @file coupon_collector.c
//! @author STEER Framework Contributors
//! @brief This file implements the TestU01 Coupon Collector test for the STEER framework.
//! @remarks Requires ANSI C99 (or better) compliant compilers.
//! @remarks Supported host operating systems: Any *nix
//! @copyright Copyright (c) 2024 Anametric, Inc. All rights reserved.
//!
//  Includes
// =================================================================================================
#include "steer.h"
#include "steer_json_utilities.h"
#include "steer_nist_sts_utilities_private.h"
#include "steer_parameters_info_utilities.h"
#include "steer_report_utilities.h"
#include "steer_report_utilities_private.h"
#include "steer_string_utilities.h"
#include "steer_string_utilities_private.h"
#include "steer_test_info_utilities.h"
#include "steer_test_shell.h"
#include "steer_utilities.h"
#include "steer_utilities_private.h"
#include "steer_value_utilities.h"
#include "cephes.h"
#include "defs.h"
#include <math.h>
#include <stdlib.h>
#include <string.h>

// =================================================================================================
//  Private constants
// =================================================================================================

#define PROGRAM_NAME        "testu01_coupon_collector_test"
#define PROGRAM_VERSION     "0.1.0"
#define TEST_NAME           "coupon collector"
#define TEST_DESCRIPTION \
"The Coupon Collector test maps random values to d categories {0,...,d-1} and counts how \
many values N are needed until all d categories have been seen (a complete coupon set). \
This is repeated n times. For d=5, E[N] = 5*(1+1/2+1/3+1/4+1/5) = 11.417. A chi-squared \
test is applied to the distribution of N across categories N=5, N=6, ..., N=14, N>=15. \
This test detects generators whose outputs fail to cover categories uniformly, revealing \
deficiencies in distributional completeness."
#define CONFIGURATION_COUNT         1
#define TESTU01_NAME                "TestU01 Crush Battery"

#define MINIMUM_BITSTREAM_COUNT     1
#define MINIMUM_BITSTREAM_LENGTH    1000000
#define MINIMUM_SIGNIFICANCE_LEVEL  0.0
#define MAXIMUM_SIGNIFICANCE_LEVEL  1.0

// Coupon Collector parameter defaults
#define CC_D_DEFAULT        5       // Number of categories (coupons)
#define CC_N_TRIALS         10000   // Number of trials

// =================================================================================================
//  Private types
// =================================================================================================

typedef struct ttestu01_couponcollectorprivatedata
{
    tSTEER_CliArguments*        cliArguments;
    tSTEER_ReportPtr            report;
    uint64_t                    bitstreamCount;
    uint64_t                    bitstreamLength;
    double                      significanceLevel;
    uint32_t                    significanceLevelPrecision;
    uint64_t                    minimumTestCountRequiredForSignificance;
    uint64_t                    predictedPassedTestCount;
    uint64_t                    predictedFailedTestCount;
    tSTEER_ConfigurationState   configurationState[CONFIGURATION_COUNT];
    uint64_t                    ones;
    uint64_t                    zeros;
    uint64_t                    numCoupons;
    double                      chiSquared;
    double                      probabilityValue;
}
tTestU01_CouponCollectorPrivateData;

// =================================================================================================
//  Private globals
// =================================================================================================

static tSTEER_InfoList gReferences = {
    1,
    {
        "P. L'Ecuyer and R. Simard, TestU01: A C Library for Empirical Testing of Random Number Generators, ACM TOMACS, 2007"
    }
};

static tSTEER_InfoList gAuthors = {
    2,
    {
        "Pierre L'Ecuyer",
        "Richard Simard"
    }
};

static tSTEER_InfoList gContributors = {
    1,
    {
        STEER_CONTRIBUTOR_GARY_WOODCOCK
    }
};

static tSTEER_InfoList gMaintainers = {
    2,
    {
        STEER_MAINTAINER_ANAMETRIC,
        STEER_MAINTAINER_SMU_DARWIN_DEASON
    }
};

static tSTEER_TestInfo gTestInfo = {
    TEST_NAME,
    TESTU01_NAME,
    TEST_DESCRIPTION,
    eSTEER_Complexity_Average,
    &gReferences,
    PROGRAM_NAME,
    PROGRAM_VERSION,
    eSTEER_InputFormat_Bitstream,
    STEER_REPOSITORY_URI,
    &gAuthors,
    &gContributors,
    &gMaintainers,
    STEER_CONTACT
};

static tSTEER_ParameterInfoList gParameterInfoList = {
    4,
    {
        {
            STEER_JSON_TAG_BITSTREAM_COUNT,
            STEER_JSON_VALUE_UNSIGNED_64_BIT_INTEGER,
            NULL,
            STEER_JSON_VALUE_BITSTREAMS,
            "1",
            "1",
            NULL
        },
        {
            STEER_JSON_TAG_BITSTREAM_LENGTH,
            STEER_JSON_VALUE_UNSIGNED_64_BIT_INTEGER,
            NULL,
            STEER_JSON_VALUE_BITS,
            "1000000",
            "1000000",
            NULL
        },
        {
            STEER_JSON_TAG_SIGNIFICANCE_LEVEL,
            STEER_JSON_VALUE_DOUBLE_PRECISION_FLOATING_POINT,
            STEER_JSON_VALUE_DEFAULT_FLOATING_POINT_PRECISION,
            NULL,
            STEER_JSON_VALUE_DEFAULT_SIGNIFICANCE_LEVEL,
            STEER_JSON_VALUE_MINIMUM_SIGNIFICANCE_LEVEL,
            STEER_JSON_VALUE_MAXIMUM_SIGNIFICANCE_LEVEL
        },
        {
            "num coupons",
            STEER_JSON_VALUE_UNSIGNED_64_BIT_INTEGER,
            NULL,
            NULL,
            "5",
            "3",
            "10"
        }
    }
};

static tSTEER_ParametersInfo gParametersInfo = {
    TEST_NAME,
    &gParameterInfoList
};

// =================================================================================================
//  Helper: extract bits from bitstream at given bit offset
// =================================================================================================
static uint32_t ExtractBits(uint8_t* buffer, uint64_t bitOffset, int numBits)
{
    uint32_t value = 0;
    int i;
    for (i = 0; i < numBits; i++)
        value = (value << 1) | buffer[bitOffset + i];
    return value;
}

// =================================================================================================
//  Helper: compute factorial
// =================================================================================================
static double Factorial(int n)
{
    double f = 1.0;
    int i;
    for (i = 2; i <= n; i++)
        f *= (double)i;
    return f;
}

// =================================================================================================
//  Helper: Stirling numbers of the second kind S(n, d)
//  S(n, d) = (1/d!) * sum_{j=0}^{d} (-1)^j * C(d,j) * (d-j)^n
// =================================================================================================
static double StirlingS2(int n, int d)
{
    double sum = 0.0;
    int j;
    for (j = 0; j <= d; j++)
    {
        // Compute C(d, j)
        double comb = Factorial(d) / (Factorial(j) * Factorial(d - j));
        double sign = (j % 2 == 0) ? 1.0 : -1.0;
        sum += sign * comb * pow((double)(d - j), (double)n);
    }
    return sum / Factorial(d);
}

// =================================================================================================
//  Helper: P(N = n) for coupon collector with d categories
//  P(N = n) = d! * S(n-1, d-1) / d^n  (for n >= d)
// =================================================================================================
static double CouponProbability(int n, int d)
{
    if (n < d) return 0.0;
    double s2 = StirlingS2(n - 1, d - 1);
    return Factorial(d) * s2 / pow((double)d, (double)n);
}

// =================================================================================================
//  RunTest
// =================================================================================================
int32_t RunTest(tTestU01_CouponCollectorPrivateData* privateData,
                uint8_t* bitstreamBuffer,
                bool* passed)
{
    int32_t result = STEER_RESULT_SUCCESS;
    uint64_t* observed = NULL;
    double* expected = NULL;
    double* probabilities = NULL;
    bool* seen = NULL;
    uint64_t bitPos = 0;
    double chiSquared = 0.0;
    uint64_t trial;
    uint64_t completedTrials = 0;
    uint64_t cat;
    uint64_t i;
    uint64_t ccD = privateData->numCoupons;
    uint64_t ccBitsPerValue = (uint64_t)ceil(log2((double)ccD));
    uint64_t ccCategories = 2 * ccD + 1;  // N=d, N=d+1, ..., N=3d-1, N>=3d
    uint64_t ccDF = ccCategories - 1;

    if (ccBitsPerValue < 1) ccBitsPerValue = 1;

    // Allocate dynamic arrays
    result = STEER_AllocateMemory(ccCategories * sizeof(uint64_t), (void**)&observed);
    if (result != STEER_RESULT_SUCCESS)
        return result;
    result = STEER_AllocateMemory(ccCategories * sizeof(double), (void**)&expected);
    if (result != STEER_RESULT_SUCCESS)
    {
        STEER_FreeMemory((void**)&observed);
        return result;
    }
    result = STEER_AllocateMemory(ccCategories * sizeof(double), (void**)&probabilities);
    if (result != STEER_RESULT_SUCCESS)
    {
        STEER_FreeMemory((void**)&observed);
        STEER_FreeMemory((void**)&expected);
        return result;
    }
    result = STEER_AllocateMemory(ccD * sizeof(bool), (void**)&seen);
    if (result != STEER_RESULT_SUCCESS)
    {
        STEER_FreeMemory((void**)&observed);
        STEER_FreeMemory((void**)&expected);
        STEER_FreeMemory((void**)&probabilities);
        return result;
    }

    memset(observed, 0, ccCategories * sizeof(uint64_t));

    // Compute theoretical probabilities for each category
    // Categories: N=d, N=d+1, ..., N=3d-1, N>=3d
    {
        double sumProb = 0.0;
        for (cat = 0; cat < ccCategories - 1; cat++)
        {
            int n = (int)(ccD + cat);
            probabilities[cat] = CouponProbability(n, (int)ccD);
            sumProb += probabilities[cat];
        }
        // Last category: N >= 3d
        probabilities[ccCategories - 1] = 1.0 - sumProb;
        if (probabilities[ccCategories - 1] < 0.0)
            probabilities[ccCategories - 1] = 0.0;
    }

    // Run trials
    for (trial = 0; trial < CC_N_TRIALS && (bitPos + ccBitsPerValue) <= privateData->bitstreamLength; trial++)
    {
        int uniqueSeen = 0;
        int count = 0;

        memset(seen, 0, ccD * sizeof(bool));

        while (uniqueSeen < (int)ccD && (bitPos + ccBitsPerValue) <= privateData->bitstreamLength)
        {
            uint32_t rawVal = ExtractBits(bitstreamBuffer, bitPos, (int)ccBitsPerValue);
            int category = rawVal % (int)ccD;
            bitPos += ccBitsPerValue;
            count++;

            if (!seen[category])
            {
                seen[category] = true;
                uniqueSeen++;
            }
        }

        if (uniqueSeen == (int)ccD)
        {
            // Categorize: N=d -> index 0, ..., N=3d-1 -> index 2d-1, N>=3d -> index 2d
            int idx = count - (int)ccD;
            if (idx < 0) idx = 0;
            if (idx >= (int)ccCategories) idx = (int)ccCategories - 1;
            observed[idx]++;
            completedTrials++;
        }
        else
        {
            break;  // Ran out of bits
        }
    }

    if (completedTrials == 0)
    {
        privateData->chiSquared = 0.0;
        privateData->probabilityValue = 0.0;
        *passed = false;
        STEER_FreeMemory((void**)&observed);
        STEER_FreeMemory((void**)&expected);
        STEER_FreeMemory((void**)&probabilities);
        STEER_FreeMemory((void**)&seen);
        return result;
    }

    // Compute expected counts
    for (i = 0; i < ccCategories; i++)
        expected[i] = probabilities[i] * (double)completedTrials;

    // Chi-squared statistic
    chiSquared = 0.0;
    for (i = 0; i < ccCategories; i++)
    {
        if (expected[i] > 0.0)
        {
            double diff = (double)observed[i] - expected[i];
            chiSquared += (diff * diff) / expected[i];
        }
    }

    privateData->chiSquared = chiSquared;

    // P-value via incomplete gamma: P = igamc(df/2, chi2/2)
    privateData->probabilityValue = cephes_igamc((double)ccDF / 2.0, chiSquared / 2.0);

    STEER_FreeMemory((void**)&observed);
    STEER_FreeMemory((void**)&expected);
    STEER_FreeMemory((void**)&probabilities);
    STEER_FreeMemory((void**)&seen);

    *passed = (privateData->probabilityValue >= privateData->significanceLevel);
    return result;
}

// =================================================================================================
//  GetTestInfo
// =================================================================================================
char* GetTestInfo(void)
{
    char* json = NULL;
    int32_t result = STEER_TestInfoToJson(&gTestInfo, &json);
    if (result == STEER_RESULT_SUCCESS)
        return json;
    else
        return NULL;
}

// =================================================================================================
//  GetParametersInfo
// =================================================================================================
char* GetParametersInfo(void)
{
    char* json = NULL;
    int32_t result = STEER_ParametersInfoToJson(&gParametersInfo, &json);
    if (result == STEER_RESULT_SUCCESS)
        return json;
    else
        return NULL;
}

// =================================================================================================
//  InitTest
// =================================================================================================
int32_t InitTest(tSTEER_CliArguments* cliArguments,
                 tSTEER_ParameterSet* parameters,
                 void** testPrivateData,
                 uint64_t* bufferSizeInBytes)
{
    int32_t result = STEER_RESULT_SUCCESS;
    tTestU01_CouponCollectorPrivateData* privData = NULL;

    *testPrivateData = NULL;
    *bufferSizeInBytes = 0;

    result = STEER_AllocateMemory(sizeof(tTestU01_CouponCollectorPrivateData), (void**)&privData);

    if (result == STEER_RESULT_SUCCESS)
    {
        uint_fast32_t i = 0;
        void* nativeValue = NULL;

        privData->cliArguments = cliArguments;

        // Set defaults for configurable parameters
        privData->numCoupons = CC_D_DEFAULT;

        for (i = 0; i < parameters->count; i++)
        {
            if (strcmp(parameters->parameter[i].name, STEER_JSON_TAG_BITSTREAM_COUNT) == 0)
            {
                result = STEER_GetNativeValue(parameters->parameter[i].dataType,
                                              parameters->parameter[i].value, &nativeValue);
                if (result == STEER_RESULT_SUCCESS)
                {
                    privData->bitstreamCount = *((uint64_t*)nativeValue);
                    STEER_FreeMemory(&nativeValue);
                }
            }
            else if (strcmp(parameters->parameter[i].name, STEER_JSON_TAG_BITSTREAM_LENGTH) == 0)
            {
                result = STEER_GetNativeValue(parameters->parameter[i].dataType,
                                              parameters->parameter[i].value, &nativeValue);
                if (result == STEER_RESULT_SUCCESS)
                {
                    privData->bitstreamLength = *((uint64_t*)nativeValue);
                    STEER_FreeMemory(&nativeValue);
                }
            }
            else if (strcmp(parameters->parameter[i].name, STEER_JSON_TAG_SIGNIFICANCE_LEVEL) == 0)
            {
                result = STEER_GetNativeValue(parameters->parameter[i].dataType,
                                              parameters->parameter[i].value, &nativeValue);
                if (result == STEER_RESULT_SUCCESS)
                {
                    privData->significanceLevel = *((double*)nativeValue);
                    STEER_FreeMemory(&nativeValue);
                }
                if (result == STEER_RESULT_SUCCESS)
                {
                    if (parameters->parameter[i].precision != NULL)
                        result = STEER_ConvertStringToUnsigned32BitInteger(
                            parameters->parameter[i].precision,
                            &(privData->significanceLevelPrecision));
                }
            }
            else if (strcmp(parameters->parameter[i].name, "num coupons") == 0)
            {
                result = STEER_GetNativeValue(parameters->parameter[i].dataType,
                                              parameters->parameter[i].value, &nativeValue);
                if (result == STEER_RESULT_SUCCESS)
                {
                    privData->numCoupons = *((uint64_t*)nativeValue);
                    STEER_FreeMemory(&nativeValue);
                }
            }
            if (result != STEER_RESULT_SUCCESS) break;
        }

        if ((privData->bitstreamCount < MINIMUM_BITSTREAM_COUNT) ||
            (privData->bitstreamLength < MINIMUM_BITSTREAM_LENGTH) ||
            ((privData->bitstreamLength % 8) != 0) ||
            (privData->significanceLevel <= MINIMUM_SIGNIFICANCE_LEVEL) ||
            (privData->significanceLevel >= MAXIMUM_SIGNIFICANCE_LEVEL))
        {
            result = STEER_CHECK_ERROR(EINVAL);
        }

        if (result == STEER_RESULT_SUCCESS)
        {
            result = STEER_GetMinimumTestCount(privData->significanceLevel,
                                               privData->bitstreamCount,
                                               &(privData->minimumTestCountRequiredForSignificance),
                                               &(privData->predictedPassedTestCount),
                                               &(privData->predictedFailedTestCount));
        }

        if (result == STEER_RESULT_SUCCESS)
        {
            privData->configurationState[0].configurationId = 0;
            *testPrivateData = (void*)privData;
            *bufferSizeInBytes = privData->bitstreamLength / 8;
        }
    }

    if (result != STEER_RESULT_SUCCESS)
        STEER_FreeMemory((void**)&privData);
    return result;
}

// =================================================================================================
//  GetConfigurationCount
// =================================================================================================
uint32_t GetConfigurationCount(void* testPrivateData)
{
    return CONFIGURATION_COUNT;
}

// =================================================================================================
//  SetReport
// =================================================================================================
int32_t SetReport(void* testPrivateData, tSTEER_ReportPtr report)
{
    ((tTestU01_CouponCollectorPrivateData*)testPrivateData)->report = report;
    return STEER_RESULT_SUCCESS;
}

// =================================================================================================
//  ExecuteTest
// =================================================================================================
int32_t ExecuteTest(void* testPrivateData,
                    const char* bitstreamId,
                    uint8_t* buffer,
                    uint64_t bufferSizeInBytes,
                    uint64_t bytesInBuffer,
                    uint64_t numZeros,
                    uint64_t numOnes)
{
    int32_t result = STEER_RESULT_SUCCESS;
    tTestU01_CouponCollectorPrivateData* privData = (tTestU01_CouponCollectorPrivateData*)testPrivateData;
    bool passed = false;
    char calculationStr[STEER_STRING_MAX_LENGTH] = { 0 };
    char criterionStr[STEER_STRING_MAX_LENGTH] = { 0 };
    uint64_t testId = 0;
    char* end = NULL;

    testId = strtoull(bitstreamId, &end, 0) - 1;

    privData->ones = numOnes;
    privData->zeros = numZeros;
    privData->configurationState[0].accumulatedOnes += numOnes;
    privData->configurationState[0].accumulatedZeros += numZeros;

    result = RunTest(privData, buffer, &passed);

    // Add calculations
    if (result == STEER_RESULT_SUCCESS)
    {
        memset(calculationStr, 0, STEER_STRING_MAX_LENGTH);
        sprintf(calculationStr, "%" PRIu64 "", numOnes);
        result = STEER_AddCalculationToTest(privData->report, 0, testId,
                                            STEER_JSON_TAG_ONES,
                                            STEER_JSON_VALUE_UNSIGNED_64_BIT_INTEGER,
                                            NULL, STEER_JSON_VALUE_BITS, calculationStr);
    }

    if (result == STEER_RESULT_SUCCESS)
    {
        memset(calculationStr, 0, STEER_STRING_MAX_LENGTH);
        sprintf(calculationStr, "%" PRIu64 "", numZeros);
        result = STEER_AddCalculationToTest(privData->report, 0, testId,
                                            STEER_JSON_TAG_ZEROS,
                                            STEER_JSON_VALUE_UNSIGNED_64_BIT_INTEGER,
                                            NULL, STEER_JSON_VALUE_BITS, calculationStr);
    }

    if (result == STEER_RESULT_SUCCESS)
    {
        memset(calculationStr, 0, STEER_STRING_MAX_LENGTH);
        sprintf(calculationStr, STEER_DEFAULT_FLOATING_POINT_STRING_FORMAT,
                STEER_DEFAULT_FLOATING_POINT_PRECISION, privData->chiSquared);
        result = STEER_AddCalculationToTest(privData->report, 0, testId,
                                            "chi squared",
                                            STEER_JSON_VALUE_DOUBLE_PRECISION_FLOATING_POINT,
                                            STEER_JSON_VALUE_DEFAULT_FLOATING_POINT_PRECISION,
                                            NULL, calculationStr);
    }

    if (result == STEER_RESULT_SUCCESS)
    {
        memset(calculationStr, 0, STEER_STRING_MAX_LENGTH);
        sprintf(calculationStr, STEER_DEFAULT_FLOATING_POINT_STRING_FORMAT,
                STEER_DEFAULT_FLOATING_POINT_PRECISION, privData->probabilityValue);
        result = STEER_AddCalculationToTest(privData->report, 0, testId,
                                            STEER_JSON_TAG_PROBABILITY_VALUE,
                                            STEER_JSON_VALUE_DOUBLE_PRECISION_FLOATING_POINT,
                                            STEER_JSON_VALUE_DEFAULT_FLOATING_POINT_PRECISION,
                                            NULL, calculationStr);
    }

    // Add criteria
    if (result == STEER_RESULT_SUCCESS)
    {
        memset(criterionStr, 0, STEER_STRING_MAX_LENGTH);
        sprintf(criterionStr, "%s of %.*f >= %s of %.*f",
                STEER_JSON_TAG_PROBABILITY_VALUE,
                STEER_DEFAULT_FLOATING_POINT_PRECISION,
                privData->probabilityValue,
                STEER_JSON_TAG_SIGNIFICANCE_LEVEL,
                privData->significanceLevelPrecision,
                privData->significanceLevel);
        result = STEER_AddCriterionToTest(privData->report, 0, testId, criterionStr,
                                          (privData->probabilityValue >= privData->significanceLevel));
    }

    // Add evaluation
    if (result == STEER_RESULT_SUCCESS)
    {
        bool eval_passed = false;
        result = STEER_AddEvaluationToTest(privData->report, 0, testId, &eval_passed);
        if (result == STEER_RESULT_SUCCESS)
        {
            privData->configurationState[0].testsRun++;
            if (eval_passed)
                privData->configurationState[0].testsPassed++;
            else
                privData->configurationState[0].testsFailed++;
        }
    }

    STEER_FreeMemory((void**)&buffer);
    return result;
}

// =================================================================================================
//  FinalizeTest
// =================================================================================================
int32_t FinalizeTest(void** testPrivateData, uint64_t suppliedNumberOfBitstreams)
{
    int32_t result = STEER_RESULT_SUCCESS;
    tTestU01_CouponCollectorPrivateData* privData = (tTestU01_CouponCollectorPrivateData*)(*testPrivateData);

    if (privData != NULL)
    {
        double probabilityValueUniformity = 0.0;
        uint64_t proportionThresholdMinimum = 0;
        uint64_t proportionThresholdMaximum = 0;

        result = STEER_NistStsAddRequiredMetricsToConfiguration(privData->report, 0,
                    suppliedNumberOfBitstreams,
                    privData->minimumTestCountRequiredForSignificance,
                    privData->configurationState[0].testsPassed,
                    privData->predictedPassedTestCount,
                    privData->configurationState[0].accumulatedOnes,
                    privData->configurationState[0].accumulatedZeros);

        if (result == STEER_RESULT_SUCCESS)
        {
            result = STEER_NistStsAddMetricsToConfiguration(privData->report, 0, false,
                        suppliedNumberOfBitstreams, privData->significanceLevel,
                        &probabilityValueUniformity,
                        &proportionThresholdMinimum, &proportionThresholdMaximum);
        }

        if (result == STEER_RESULT_SUCCESS)
        {
            result = STEER_AddConfusionMatrixMetricsToConfiguration(privData->report, 0,
                        privData->minimumTestCountRequiredForSignificance,
                        privData->configurationState[0].testsRun,
                        privData->configurationState[0].testsPassed,
                        privData->configurationState[0].testsFailed,
                        privData->predictedPassedTestCount,
                        privData->predictedFailedTestCount);
        }

        if (result == STEER_RESULT_SUCCESS)
        {
            result = STEER_NistStsAddRequiredCriterionToConfiguration(privData->report, 0,
                        suppliedNumberOfBitstreams,
                        privData->configurationState[0].testsPassed,
                        privData->significanceLevel,
                        privData->significanceLevelPrecision,
                        privData->minimumTestCountRequiredForSignificance);
        }

        if (result == STEER_RESULT_SUCCESS)
        {
            result = STEER_NistStsAddCriteriaToConfiguration(privData->report, 0,
                        probabilityValueUniformity,
                        proportionThresholdMinimum, proportionThresholdMaximum,
                        privData->configurationState[0].testsRun,
                        privData->configurationState[0].testsPassed);
        }

        if (result == STEER_RESULT_SUCCESS)
            result = STEER_AddEvaluationToConfiguration(privData->report, 0);

        STEER_FreeMemory((void**)testPrivateData);
    }
    return result;
}

// =================================================================================================
//  main
// =================================================================================================
int main(int argc, const char* argv[])
{
    return STEER_Run(PROGRAM_NAME, argc, argv,
                     GetTestInfo, GetParametersInfo,
                     InitTest, GetConfigurationCount,
                     SetReport, ExecuteTest, FinalizeTest);
}

// =================================================================================================
